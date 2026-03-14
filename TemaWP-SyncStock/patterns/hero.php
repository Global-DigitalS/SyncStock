<?php
/**
 * Title: Hero Principal
 * Slug: syncstock/hero
 * Categories: syncstock-hero
 * Keywords: hero, banner, inicio
 * Description: Sección hero principal con título, subtítulo y botones CTA.
 */
?>

<!-- wp:group {"style":{"spacing":{"padding":{"top":"var:preset|spacing|100","bottom":"var:preset|spacing|90"}}},"gradient":"hero-gradient","layout":{"type":"constrained","contentSize":"800px"}} -->
<div class="wp-block-group has-hero-gradient-gradient-background has-background" style="padding-top:var(--wp--preset--spacing--100);padding-bottom:var(--wp--preset--spacing--90)">

	<!-- wp:group {"layout":{"type":"constrained","contentSize":"700px"}} -->
	<div class="wp-block-group">

		<!-- wp:group {"layout":{"type":"flex","justifyContent":"center"}} -->
		<div class="wp-block-group">
			<!-- wp:paragraph {"className":"syncstock-badge","style":{"spacing":{"padding":{"top":"0.25rem","bottom":"0.25rem","left":"0.75rem","right":"0.75rem"}},"border":{"radius":"9999px"}},"backgroundColor":"brand-100","textColor":"brand-700","fontSize":"xs"} -->
			<p class="syncstock-badge has-brand-700-color has-brand-100-background-color has-text-color has-background has-xs-font-size" style="border-radius:9999px;padding-top:0.25rem;padding-right:0.75rem;padding-bottom:0.25rem;padding-left:0.75rem">Plataforma B2B de sincronización</p>
			<!-- /wp:paragraph -->
		</div>
		<!-- /wp:group -->

		<!-- wp:heading {"textAlign":"center","level":1,"style":{"spacing":{"margin":{"top":"var:preset|spacing|50"}}},"fontSize":"hero"} -->
		<h1 class="wp-block-heading has-text-align-center has-hero-font-size" style="margin-top:var(--wp--preset--spacing--50)">Sincroniza tu inventario en <mark style="background-color:transparent" class="has-inline-color has-brand-600-color">tiempo real</mark></h1>
		<!-- /wp:heading -->

		<!-- wp:paragraph {"align":"center","style":{"spacing":{"margin":{"top":"var:preset|spacing|50"}}},"textColor":"slate-600","fontSize":"large"} -->
		<p class="has-text-align-center has-slate-600-color has-text-color has-large-font-size" style="margin-top:var(--wp--preset--spacing--50)">Conecta proveedores FTP, SFTP y URL con tus tiendas WooCommerce, Shopify y PrestaShop. Gestiona catálogos, precios y stock desde un solo lugar.</p>
		<!-- /wp:paragraph -->

		<!-- wp:buttons {"layout":{"type":"flex","justifyContent":"center"},"style":{"spacing":{"margin":{"top":"var:preset|spacing|60"},"blockGap":"var:preset|spacing|40"}}} -->
		<div class="wp-block-buttons" style="margin-top:var(--wp--preset--spacing--60)">
			<!-- wp:button {"backgroundColor":"brand-600","style":{"border":{"radius":"0.5rem"},"spacing":{"padding":{"top":"0.75rem","bottom":"0.75rem","left":"1.75rem","right":"1.75rem"}}},"fontSize":"medium"} -->
			<div class="wp-block-button"><a class="wp-block-button__link has-brand-600-background-color has-background has-medium-font-size" style="border-radius:0.5rem;padding-top:0.75rem;padding-right:1.75rem;padding-bottom:0.75rem;padding-left:1.75rem">Empezar Gratis →</a></div>
			<!-- /wp:button -->

			<!-- wp:button {"className":"is-style-outline","style":{"border":{"radius":"0.5rem"},"spacing":{"padding":{"top":"0.75rem","bottom":"0.75rem","left":"1.75rem","right":"1.75rem"}}},"fontSize":"medium"} -->
			<div class="wp-block-button is-style-outline"><a class="wp-block-button__link has-medium-font-size" style="border-radius:0.5rem;padding-top:0.75rem;padding-right:1.75rem;padding-bottom:0.75rem;padding-left:1.75rem">Ver Demo</a></div>
			<!-- /wp:button -->
		</div>
		<!-- /wp:buttons -->

		<!-- wp:paragraph {"align":"center","style":{"spacing":{"margin":{"top":"var:preset|spacing|40"}}},"textColor":"slate-400","fontSize":"small"} -->
		<p class="has-text-align-center has-slate-400-color has-text-color has-small-font-size" style="margin-top:var(--wp--preset--spacing--40)">Sin tarjeta de crédito · Configuración en 5 minutos · Soporte incluido</p>
		<!-- /wp:paragraph -->

	</div>
	<!-- /wp:group -->

</div>
<!-- /wp:group -->
