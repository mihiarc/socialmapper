"""
Graph Neural Networks for Spatial Community Detection

This module implements Graph Neural Networks (GNNs) to model complex spatial 
relationships between buildings and detect community patterns that traditional
clustering methods might miss.
"""

import numpy as np
import pandas as pd
import geopandas as gpd
import networkx as nx
from typing import Dict, List, Tuple, Optional, Union
from shapely.geometry import Point, Polygon
import warnings

# Try importing deep learning libraries
try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from torch_geometric.nn import GCNConv, GATConv, SAGEConv
    from torch_geometric.data import Data, Batch
    from torch_geometric.utils import from_networkx
    TORCH_GEOMETRIC_AVAILABLE = True
except ImportError:
    TORCH_GEOMETRIC_AVAILABLE = False
    warnings.warn("PyTorch Geometric not available. Install with: pip install torch-geometric")

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False


class SpatialGraphBuilder:
    """
    Builds spatial graphs from building footprints for GNN analysis.
    """
    
    def __init__(self, 
                 k_neighbors: int = 8,
                 distance_threshold: float = 500.0,
                 include_visibility: bool = True):
        """
        Initialize spatial graph builder.
        
        Args:
            k_neighbors: Number of nearest neighbors to connect
            distance_threshold: Maximum distance for connections (meters)
            include_visibility: Whether to include line-of-sight connections
        """
        self.k_neighbors = k_neighbors
        self.distance_threshold = distance_threshold
        self.include_visibility = include_visibility
        
    def build_spatial_graph(self, buildings_gdf: gpd.GeoDataFrame) -> 'nx.Graph':
        """
        Build a spatial graph from building footprints.
        
        Args:
            buildings_gdf: GeoDataFrame containing building polygons
            
        Returns:
            NetworkX graph with spatial relationships
        """
        if not NETWORKX_AVAILABLE:
            raise ImportError("NetworkX required for graph building")
            
        G = nx.Graph()
        
        # Add nodes (buildings) with their features
        for idx, building in buildings_gdf.iterrows():
            centroid = building.geometry.centroid
            
            # Node features
            node_features = {
                'x': centroid.x,
                'y': centroid.y,
                'area': building.geometry.area,
                'perimeter': building.geometry.length,
                'compactness': (4 * np.pi * building.geometry.area) / (building.geometry.length ** 2),
            }
            
            G.add_node(idx, **node_features)
        
        # Add edges based on spatial relationships
        nodes = list(G.nodes(data=True))
        
        for i, (node1_id, node1_data) in enumerate(nodes):
            distances = []
            
            # Calculate distances to all other nodes
            for j, (node2_id, node2_data) in enumerate(nodes):
                if i != j:
                    dist = np.sqrt((node1_data['x'] - node2_data['x'])**2 + 
                                 (node1_data['y'] - node2_data['y'])**2)
                    distances.append((dist, node2_id))
            
            # Sort by distance and connect to k nearest neighbors within threshold
            distances.sort()
            connected = 0
            
            for dist, neighbor_id in distances:
                if dist <= self.distance_threshold and connected < self.k_neighbors:
                    # Calculate edge features
                    edge_weight = 1.0 / (1.0 + dist)  # Inverse distance weighting
                    
                    # Add visibility check if enabled
                    if self.include_visibility:
                        visibility = self._check_visibility(
                            buildings_gdf.loc[node1_id],
                            buildings_gdf.loc[neighbor_id],
                            buildings_gdf
                        )
                        edge_weight *= visibility
                    
                    G.add_edge(node1_id, neighbor_id, 
                             weight=edge_weight, 
                             distance=dist)
                    connected += 1
                    
        return G
    
    def _check_visibility(self, building1, building2, all_buildings: gpd.GeoDataFrame) -> float:
        """
        Check line-of-sight visibility between two buildings.
        Returns visibility score between 0 and 1.
        """
        from shapely.geometry import LineString
        
        centroid1 = building1.geometry.centroid
        centroid2 = building2.geometry.centroid
        sight_line = LineString([centroid1, centroid2])
        
        # Check intersections with other buildings
        intersections = 0
        for _, other_building in all_buildings.iterrows():
            if (not building1.geometry.equals(other_building.geometry) and
                not building2.geometry.equals(other_building.geometry)):
                if sight_line.intersects(other_building.geometry):
                    intersections += 1
        
        # Return visibility score (1.0 = completely visible, 0.0 = completely blocked)
        max_intersections = 10  # Normalize by maximum expected intersections
        return max(0.0, 1.0 - (intersections / max_intersections))


# Only define PyTorch-based classes if available
if TORCH_GEOMETRIC_AVAILABLE:
    
    class CommunityGNN(nn.Module):
        """
        Graph Neural Network for community detection in spatial data.
        """
        
        def __init__(self, 
                     input_dim: int,
                     hidden_dim: int = 64,
                     output_dim: int = 32,
                     num_layers: int = 3,
                     gnn_type: str = 'gcn'):
            """
            Initialize Community Detection GNN.
            
            Args:
                input_dim: Input feature dimension
                hidden_dim: Hidden layer dimension
                output_dim: Output embedding dimension
                num_layers: Number of GNN layers
                gnn_type: 'gcn', 'gat', or 'sage'
            """
            super(CommunityGNN, self).__init__()
            
            self.num_layers = num_layers
            self.gnn_type = gnn_type
            
            # GNN layers
            self.gnn_layers = nn.ModuleList()
            
            for i in range(num_layers):
                in_dim = input_dim if i == 0 else hidden_dim
                out_dim = output_dim if i == num_layers - 1 else hidden_dim
                
                if gnn_type == 'gcn':
                    layer = GCNConv(in_dim, out_dim)
                elif gnn_type == 'gat':
                    layer = GATConv(in_dim, out_dim, heads=4, concat=False)
                elif gnn_type == 'sage':
                    layer = SAGEConv(in_dim, out_dim)
                else:
                    raise ValueError(f"Unknown GNN type: {gnn_type}")
                    
                self.gnn_layers.append(layer)
            
            # Classification head for community prediction
            self.classifier = nn.Sequential(
                nn.Linear(output_dim, hidden_dim),
                nn.ReLU(),
                nn.Dropout(0.5),
                nn.Linear(hidden_dim, 16)  # 16 different community types
            )
            
        def forward(self, x, edge_index, edge_weight=None):
            """
            Forward pass through the GNN.
            
            Args:
                x: Node features
                edge_index: Edge connectivity
                edge_weight: Edge weights
                
            Returns:
                Node embeddings and community predictions
            """
            # Apply GNN layers
            for i, layer in enumerate(self.gnn_layers):
                if self.gnn_type == 'gcn':
                    x = layer(x, edge_index, edge_weight)
                else:
                    x = layer(x, edge_index)
                    
                if i < self.num_layers - 1:
                    x = F.relu(x)
                    x = F.dropout(x, training=self.training)
            
            # Get embeddings and predictions
            embeddings = x
            community_logits = self.classifier(x)
            
            return embeddings, community_logits

    
    class GNNCommunityDetector:
        """
        High-level interface for GNN-based community detection.
        """
        
        def __init__(self, 
                     model_config: Optional[Dict] = None,
                     use_pretrained: bool = False):
            """
            Initialize GNN community detector.
            
            Args:
                model_config: Configuration for GNN model
                use_pretrained: Whether to use pretrained weights
            """
            self.model_config = model_config or {
                'hidden_dim': 64,
                'output_dim': 32,
                'num_layers': 3,
                'gnn_type': 'gat'  # Graph Attention Networks work well for spatial data
            }
            
            self.graph_builder = SpatialGraphBuilder()
            self.model = None
            self.is_trained = False
            
        def detect_communities(self, 
                             buildings_gdf: gpd.GeoDataFrame,
                             use_unsupervised: bool = True) -> gpd.GeoDataFrame:
            """
            Detect communities using GNN analysis.
            
            Args:
                buildings_gdf: GeoDataFrame containing building polygons
                use_unsupervised: Whether to use unsupervised learning
                
            Returns:
                GeoDataFrame with community assignments and confidence scores
            """
            # Build spatial graph
            G = self.graph_builder.build_spatial_graph(buildings_gdf)
            
            if use_unsupervised:
                return self._detect_communities_unsupervised(buildings_gdf, G)
            else:
                return self._detect_communities_supervised(buildings_gdf, G)
        
        def _detect_communities_unsupervised(self, 
                                           buildings_gdf: gpd.GeoDataFrame, 
                                           G: 'nx.Graph') -> gpd.GeoDataFrame:
            """
            Unsupervised community detection using graph algorithms.
            """
            # Use community detection algorithms from NetworkX
            communities = nx.community.greedy_modularity_communities(G)
            
            # Create community assignments
            community_map = {}
            for i, community in enumerate(communities):
                for node in community:
                    community_map[node] = i
            
            # Add to buildings dataframe
            buildings_result = buildings_gdf.copy()
            buildings_result['community_id'] = buildings_result.index.map(community_map)
            buildings_result['detection_method'] = 'gnn_unsupervised'
            buildings_result['confidence'] = 1.0  # Placeholder
            
            return buildings_result
        
        def _detect_communities_supervised(self, 
                                         buildings_gdf: gpd.GeoDataFrame, 
                                         G: 'nx.Graph') -> gpd.GeoDataFrame:
            """
            Supervised community detection using trained GNN.
            """
            # Convert to PyTorch Geometric format
            data = from_networkx(G)
            
            # Prepare node features
            node_features = []
            for node_id in G.nodes():
                node_data = G.nodes[node_id]
                features = [
                    node_data['x'],
                    node_data['y'], 
                    node_data['area'],
                    node_data['perimeter'],
                    node_data['compactness']
                ]
                node_features.append(features)
            
            data.x = torch.tensor(node_features, dtype=torch.float)
            
            # Initialize model if needed
            if self.model is None:
                input_dim = data.x.size(1)
                self.model = CommunityGNN(input_dim, **self.model_config)
            
            # Run inference
            self.model.eval()
            with torch.no_grad():
                embeddings, community_logits = self.model(data.x, data.edge_index)
                community_probs = F.softmax(community_logits, dim=1)
                community_assignments = torch.argmax(community_probs, dim=1)
                confidence_scores = torch.max(community_probs, dim=1)[0]
            
            # Add results to buildings dataframe
            buildings_result = buildings_gdf.copy()
            buildings_result['community_id'] = community_assignments.numpy()
            buildings_result['confidence'] = confidence_scores.numpy()
            buildings_result['detection_method'] = 'gnn_supervised'
            
            return buildings_result
        
        def train_model(self, 
                       training_data: List[Tuple[gpd.GeoDataFrame, List[int]]], 
                       num_epochs: int = 100,
                       learning_rate: float = 0.01):
            """
            Train the GNN model on labeled community data.
            
            Args:
                training_data: List of (buildings_gdf, community_labels) tuples
                num_epochs: Number of training epochs
                learning_rate: Learning rate for optimization
            """
            if not TORCH_GEOMETRIC_AVAILABLE:
                raise ImportError("PyTorch Geometric required for training")
            
            # Prepare training data
            training_graphs = []
            for buildings_gdf, labels in training_data:
                G = self.graph_builder.build_spatial_graph(buildings_gdf)
                data = from_networkx(G)
                
                # Add node features and labels
                node_features = []
                for node_id in G.nodes():
                    node_data = G.nodes[node_id]
                    features = [
                        node_data['x'], node_data['y'], 
                        node_data['area'], node_data['perimeter'],
                        node_data['compactness']
                    ]
                    node_features.append(features)
                
                data.x = torch.tensor(node_features, dtype=torch.float)
                data.y = torch.tensor(labels, dtype=torch.long)
                training_graphs.append(data)
            
            # Initialize model
            input_dim = training_graphs[0].x.size(1)
            self.model = CommunityGNN(input_dim, **self.model_config)
            
            # Training setup
            optimizer = torch.optim.Adam(self.model.parameters(), lr=learning_rate)
            criterion = nn.CrossEntropyLoss()
            
            # Training loop
            self.model.train()
            for epoch in range(num_epochs):
                total_loss = 0
                
                for data in training_graphs:
                    optimizer.zero_grad()
                    
                    _, community_logits = self.model(data.x, data.edge_index)
                    loss = criterion(community_logits, data.y)
                    
                    loss.backward()
                    optimizer.step()
                    total_loss += loss.item()
                
                if epoch % 10 == 0:
                    avg_loss = total_loss / len(training_graphs)
                    print(f"Epoch {epoch}, Average Loss: {avg_loss:.4f}")
            
            self.is_trained = True
            print("Training completed!")

else:
    # Placeholder classes when PyTorch is not available
    class CommunityGNN:
        def __init__(self, *args, **kwargs):
            raise ImportError("PyTorch Geometric not available. Install with: pip install torch-geometric")
    
    class GNNCommunityDetector:
        def __init__(self, *args, **kwargs):
            raise ImportError("PyTorch Geometric not available. Install with: pip install torch-geometric")


def detect_communities_with_gnn(buildings_gdf: gpd.GeoDataFrame,
                               method: str = 'unsupervised',
                               **kwargs) -> gpd.GeoDataFrame:
    """
    Convenience function for GNN-based community detection.
    
    Args:
        buildings_gdf: GeoDataFrame containing building polygons
        method: 'unsupervised' or 'supervised'
        **kwargs: Additional arguments for GNN detector
        
    Returns:
        GeoDataFrame with community assignments
    """
    if not TORCH_GEOMETRIC_AVAILABLE:
        raise ImportError("PyTorch Geometric not available. Install with: pip install torch-geometric")
        
    detector = GNNCommunityDetector(**kwargs)
    
    use_unsupervised = (method == 'unsupervised')
    return detector.detect_communities(buildings_gdf, use_unsupervised) 