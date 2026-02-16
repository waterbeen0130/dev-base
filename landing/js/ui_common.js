$(function() {
    var wrap = document.getElementById('wrap');
    if (!wrap) {
        return;
    }

    wrap.classList.add('section_on');

    if (!('IntersectionObserver' in window)) {
        return;
    }

    var targets = wrap.querySelectorAll('[data-delay]');
    var observer = new window.IntersectionObserver(
        function(entries) {
            entries.forEach(function(entry) {
                if (!entry.isIntersecting) {
                    return;
                }
                entry.target.classList.add('section_on');
                var delay = parseFloat(entry.target.getAttribute('data-delay') || 0);
                if (!Number.isNaN(delay)) {
                    entry.target.style.transitionDelay = delay + 's';
                }
            });
        },
        {
            rootMargin: '0px 0px -12% 0px',
            threshold: 0.05,
        }
    );

    targets.forEach(function(item) {
        observer.observe(item);
    });
});
