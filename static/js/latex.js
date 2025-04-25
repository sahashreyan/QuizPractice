document.addEventListener('DOMContentLoaded', function() {
    // Configure MathJax
    window.MathJax = {
        tex: {
            inlineMath: [['$', '$'], ['\\(', '\\)']],
            displayMath: [['$$', '$$'], ['\\[', '\\]']],
            processEscapes: true,
            processEnvironments: true
        },
        options: {
            skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre']
        }
    };

    // Add event listener to all elements with question-text class
    document.addEventListener('input', function(e) {
        if (e.target.classList.contains('question-text') || 
            e.target.classList.contains('option-text')) {
            
            // Delayed rendering to avoid performance issues when typing
            clearTimeout(e.target.latexTimeout);
            e.target.latexTimeout = setTimeout(function() {
                if (window.MathJax) {
                    MathJax.typeset([e.target.parentNode]);
                }
            }, 500);
        }
    });

    // Helper function to render LaTeX in a specific element
    window.renderLatex = function(element) {
        if (window.MathJax) {
            MathJax.typeset([element]);
        }
    };
});