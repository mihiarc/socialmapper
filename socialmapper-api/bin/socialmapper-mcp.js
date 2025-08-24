#!/usr/bin/env node

const { spawn } = require('child_process');
const path = require('path');

// Get the MCP server URL from command line args or default
const serverUrl = process.argv[2] || 'http://localhost:8000/mcp';

// Path to the Python bridge script
const bridgePath = path.join(__dirname, '..', 'fastapi_mcp_bridge.py');

console.error(`SocialMapper MCP Server starting...`);
console.error(`Server URL: ${serverUrl}`);
console.error(`Bridge: ${bridgePath}`);

// Check if uv is available, fallback to python
function checkCommand(command) {
  return new Promise((resolve) => {
    const child = spawn('which', [command], { stdio: 'pipe' });
    child.on('close', (code) => {
      resolve(code === 0);
    });
  });
}

async function startBridge() {
  let pythonCmd, args;
  
  // Try uv first (preferred for SocialMapper)
  if (await checkCommand('uv')) {
    pythonCmd = 'uv';
    args = ['run', '--with', 'httpx', '--with', 'asyncio', 'python', bridgePath, serverUrl];
    console.error('Using uv to run Python bridge with dependencies...');
  } 
  // Try pip install approach
  else if (await checkCommand('python3')) {
    console.error('Installing required dependencies...');
    // Try to install httpx if needed
    try {
      await new Promise((resolve, reject) => {
        const pip = spawn('python3', ['-m', 'pip', 'install', 'httpx'], { stdio: 'pipe' });
        pip.on('close', (code) => {
          if (code === 0) resolve();
          else reject(new Error('pip install failed'));
        });
      });
    } catch (e) {
      console.error('Warning: Could not install httpx. Make sure dependencies are available.');
    }
    
    pythonCmd = 'python3';
    args = [bridgePath, serverUrl];
    console.error('Using python3 to run bridge...');
  }
  else if (await checkCommand('python')) {
    pythonCmd = 'python';
    args = [bridgePath, serverUrl];
    console.error('Using python to run bridge...');
  }
  else {
    console.error('Error: No Python interpreter found. Please install Python 3.11+ or uv.');
    console.error('For best experience, install uv: https://docs.astral.sh/uv/getting-started/installation/');
    process.exit(1);
  }
  
  // Spawn the Python bridge
  const bridge = spawn(pythonCmd, args, {
    stdio: ['pipe', 'pipe', 'inherit'],
    cwd: path.dirname(bridgePath)
  });
  
  // Forward stdin to bridge
  process.stdin.pipe(bridge.stdin);
  
  // Forward bridge stdout to our stdout
  bridge.stdout.pipe(process.stdout);
  
  // Handle errors
  bridge.on('error', (err) => {
    console.error(`Bridge error: ${err.message}`);
    process.exit(1);
  });
  
  bridge.on('close', (code) => {
    console.error(`Bridge exited with code ${code}`);
    process.exit(code);
  });
  
  // Handle process signals
  process.on('SIGINT', () => {
    bridge.kill('SIGINT');
  });
  
  process.on('SIGTERM', () => {
    bridge.kill('SIGTERM');
  });
}

// Start the bridge
startBridge().catch((err) => {
  console.error(`Failed to start bridge: ${err.message}`);
  process.exit(1);
});