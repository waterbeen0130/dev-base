$(document).ready(function(){
    gsap.registerPlugin(ScrollTrigger);
    const sectionData = [
        { selector: ".motion_section", top: "70%", className: "motion_section section_on" },
    ];

    setTimeout(() => {
        sectionData.forEach(data => {
            // 해당 선택자의 요소가 존재하는지 먼저 확인
            if (document.querySelector(data.selector)) {
                gsap.set(data.selector, {
                    scrollTrigger: {
                        trigger: data.selector,
                        start: `top ${data.top}`,
                        //markers: true,
                        onEnter: () => document.querySelector(data.selector).classList.add(data.className)
                    }
                });
            }
        });
    }, 500);

    $('[data-delay]').each(function() {
        var delay = $(this).attr('data-delay');
        if (!isNaN(delay)) {
            $(this).css('transition-delay', delay + 's');
        }
    });

});