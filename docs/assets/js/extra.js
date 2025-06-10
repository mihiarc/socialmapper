// SocialMapper Documentation Custom JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Add any custom JavaScript functionality here
    
    // Example: Enhanced code copy button feedback
    document.addEventListener('copy', function(e) {
        // Show a brief success message when code is copied
        const button = e.target.closest('.md-clipboard');
        if (button) {
            const originalTitle = button.title;
            button.title = 'Copied!';
            setTimeout(() => {
                button.title = originalTitle;
            }, 2000);
        }
    });
    
    // Future enhancements can be added here
}); 