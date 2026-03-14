/**
 * SyncStock - Scripts del tema
 *
 * @package SyncStock
 * @since 1.0.0
 */

(function () {
	'use strict';

	/**
	 * Header scroll effect
	 */
	function initHeaderScroll() {
		var header = document.querySelector('.syncstock-header');
		if (!header) return;

		var scrollThreshold = 10;

		function onScroll() {
			if (window.scrollY > scrollThreshold) {
				header.classList.add('is-scrolled');
			} else {
				header.classList.remove('is-scrolled');
			}
		}

		window.addEventListener('scroll', onScroll, { passive: true });
		onScroll();
	}

	/**
	 * Fade-in animation on scroll (Intersection Observer)
	 */
	function initFadeIn() {
		var elements = document.querySelectorAll('.syncstock-fade-in');
		if (!elements.length) return;

		if (!('IntersectionObserver' in window)) {
			elements.forEach(function (el) {
				el.classList.add('is-visible');
			});
			return;
		}

		var observer = new IntersectionObserver(
			function (entries) {
				entries.forEach(function (entry) {
					if (entry.isIntersecting) {
						entry.target.classList.add('is-visible');
						observer.unobserve(entry.target);
					}
				});
			},
			{ threshold: 0.1, rootMargin: '0px 0px -50px 0px' }
		);

		elements.forEach(function (el) {
			observer.observe(el);
		});
	}

	/**
	 * Smooth scroll for anchor links
	 */
	function initSmoothScroll() {
		document.querySelectorAll('a[href^="#"]').forEach(function (link) {
			link.addEventListener('click', function (e) {
				var targetId = this.getAttribute('href');
				if (targetId === '#') return;

				var target = document.querySelector(targetId);
				if (!target) return;

				e.preventDefault();
				var headerHeight = document.querySelector('.syncstock-header')
					? document.querySelector('.syncstock-header').offsetHeight
					: 0;
				var targetPosition =
					target.getBoundingClientRect().top +
					window.pageYOffset -
					headerHeight -
					20;

				window.scrollTo({
					top: targetPosition,
					behavior: 'smooth',
				});
			});
		});
	}

	/**
	 * Initialize on DOM ready
	 */
	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', init);
	} else {
		init();
	}

	function init() {
		initHeaderScroll();
		initFadeIn();
		initSmoothScroll();
	}
})();
