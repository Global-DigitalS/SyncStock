<?php
/**
 * Title: Precios
 * Slug: syncstock/pricing
 * Categories: syncstock-pricing
 * Keywords: precios, planes, suscripción
 * Description: Tabla de precios con tres planes.
 */
?>

<!-- wp:group {"style":{"spacing":{"padding":{"top":"var:preset|spacing|90","bottom":"var:preset|spacing|90"}}},"layout":{"type":"constrained","contentSize":"1200px"}} -->
<div class="wp-block-group" style="padding-top:var(--wp--preset--spacing--90);padding-bottom:var(--wp--preset--spacing--90)">

	<!-- wp:group {"layout":{"type":"constrained","contentSize":"600px"}} -->
	<div class="wp-block-group">
		<!-- wp:heading {"textAlign":"center","level":2,"fontSize":"5x-large"} -->
		<h2 class="wp-block-heading has-text-align-center has-5-x-large-font-size">Planes simples y transparentes</h2>
		<!-- /wp:heading -->

		<!-- wp:paragraph {"align":"center","textColor":"slate-500","fontSize":"large"} -->
		<p class="has-text-align-center has-slate-500-color has-text-color has-large-font-size">Sin costes ocultos. Elige el plan que mejor se adapte a tu negocio.</p>
		<!-- /wp:paragraph -->
	</div>
	<!-- /wp:group -->

	<!-- wp:columns {"style":{"spacing":{"margin":{"top":"var:preset|spacing|70"},"blockGap":{"left":"var:preset|spacing|50"}}}} -->
	<div class="wp-block-columns" style="margin-top:var(--wp--preset--spacing--70)">

		<!-- wp:column -->
		<div class="wp-block-column">
			<!-- wp:group {"className":"syncstock-card","style":{"spacing":{"padding":{"top":"var:preset|spacing|70","bottom":"var:preset|spacing|70","left":"var:preset|spacing|60","right":"var:preset|spacing|60"}},"border":{"radius":"0.75rem"}},"backgroundColor":"white","layout":{"type":"constrained"}} -->
			<div class="wp-block-group syncstock-card has-white-background-color has-background" style="border-radius:0.75rem;padding-top:var(--wp--preset--spacing--70);padding-right:var(--wp--preset--spacing--60);padding-bottom:var(--wp--preset--spacing--70);padding-left:var(--wp--preset--spacing--60)">

				<!-- wp:heading {"level":3,"textColor":"slate-700","fontSize":"x-large"} -->
				<h3 class="wp-block-heading has-slate-700-color has-text-color has-x-large-font-size">Starter</h3>
				<!-- /wp:heading -->

				<!-- wp:group {"layout":{"type":"flex","flexWrap":"nowrap","verticalAlignment":"bottom"}} -->
				<div class="wp-block-group">
					<!-- wp:paragraph {"style":{"typography":{"fontWeight":"800","lineHeight":"1"}},"fontSize":"4x-large","fontFamily":"heading"} -->
					<p class="has-heading-font-family has-4-x-large-font-size" style="font-weight:800;line-height:1">29€</p>
					<!-- /wp:paragraph -->
					<!-- wp:paragraph {"textColor":"slate-400","fontSize":"small"} -->
					<p class="has-slate-400-color has-text-color has-small-font-size">/mes</p>
					<!-- /wp:paragraph -->
				</div>
				<!-- /wp:group -->

				<!-- wp:paragraph {"textColor":"slate-500","fontSize":"small","style":{"spacing":{"margin":{"top":"var:preset|spacing|30"}}}} -->
				<p class="has-slate-500-color has-text-color has-small-font-size" style="margin-top:var(--wp--preset--spacing--30)">Ideal para pequeñas empresas que empiezan con e-commerce.</p>
				<!-- /wp:paragraph -->

				<!-- wp:separator {"backgroundColor":"slate-200","style":{"spacing":{"margin":{"top":"var:preset|spacing|50","bottom":"var:preset|spacing|50"}}}} -->
				<hr class="wp-block-separator has-text-color has-slate-200-color has-alpha-channel-opacity has-slate-200-background-color has-background" style="margin-top:var(--wp--preset--spacing--50);margin-bottom:var(--wp--preset--spacing--50)"/>
				<!-- /wp:separator -->

				<!-- wp:list {"style":{"typography":{"lineHeight":"2.2"}},"textColor":"slate-600","fontSize":"small","className":"is-style-no-bullets"} -->
				<ul style="line-height:2.2" class="is-style-no-bullets has-slate-600-color has-text-color has-small-font-size">
					<li>✓ 10 proveedores</li>
					<li>✓ 5 catálogos</li>
					<li>✓ 2 tiendas</li>
					<li>✓ Sincronización cada 6h</li>
					<li>✓ Soporte por email</li>
				</ul>
				<!-- /wp:list -->

				<!-- wp:buttons {"style":{"spacing":{"margin":{"top":"var:preset|spacing|50"}}}} -->
				<div class="wp-block-buttons" style="margin-top:var(--wp--preset--spacing--50)">
					<!-- wp:button {"width":100,"className":"is-style-outline","style":{"border":{"radius":"0.5rem"}}} -->
					<div class="wp-block-button has-custom-width wp-block-button__width-100 is-style-outline"><a class="wp-block-button__link" style="border-radius:0.5rem">Elegir Starter</a></div>
					<!-- /wp:button -->
				</div>
				<!-- /wp:buttons -->

			</div>
			<!-- /wp:group -->
		</div>
		<!-- /wp:column -->

		<!-- wp:column -->
		<div class="wp-block-column">
			<!-- wp:group {"className":"syncstock-card syncstock-card-featured","style":{"spacing":{"padding":{"top":"var:preset|spacing|70","bottom":"var:preset|spacing|70","left":"var:preset|spacing|60","right":"var:preset|spacing|60"}},"border":{"radius":"0.75rem"}},"backgroundColor":"white","layout":{"type":"constrained"}} -->
			<div class="wp-block-group syncstock-card syncstock-card-featured has-white-background-color has-background" style="border-radius:0.75rem;padding-top:var(--wp--preset--spacing--70);padding-right:var(--wp--preset--spacing--60);padding-bottom:var(--wp--preset--spacing--70);padding-left:var(--wp--preset--spacing--60)">

				<!-- wp:group {"layout":{"type":"flex","justifyContent":"space-between"}} -->
				<div class="wp-block-group">
					<!-- wp:heading {"level":3,"textColor":"slate-700","fontSize":"x-large"} -->
					<h3 class="wp-block-heading has-slate-700-color has-text-color has-x-large-font-size">Professional</h3>
					<!-- /wp:heading -->

					<!-- wp:paragraph {"className":"syncstock-badge","style":{"spacing":{"padding":{"top":"0.15rem","bottom":"0.15rem","left":"0.5rem","right":"0.5rem"}},"border":{"radius":"9999px"}},"backgroundColor":"brand-600","textColor":"white","fontSize":"xs"} -->
					<p class="syncstock-badge has-white-color has-brand-600-background-color has-text-color has-background has-xs-font-size" style="border-radius:9999px;padding-top:0.15rem;padding-right:0.5rem;padding-bottom:0.15rem;padding-left:0.5rem">Popular</p>
					<!-- /wp:paragraph -->
				</div>
				<!-- /wp:group -->

				<!-- wp:group {"layout":{"type":"flex","flexWrap":"nowrap","verticalAlignment":"bottom"}} -->
				<div class="wp-block-group">
					<!-- wp:paragraph {"style":{"typography":{"fontWeight":"800","lineHeight":"1"}},"fontSize":"4x-large","fontFamily":"heading"} -->
					<p class="has-heading-font-family has-4-x-large-font-size" style="font-weight:800;line-height:1">79€</p>
					<!-- /wp:paragraph -->
					<!-- wp:paragraph {"textColor":"slate-400","fontSize":"small"} -->
					<p class="has-slate-400-color has-text-color has-small-font-size">/mes</p>
					<!-- /wp:paragraph -->
				</div>
				<!-- /wp:group -->

				<!-- wp:paragraph {"textColor":"slate-500","fontSize":"small","style":{"spacing":{"margin":{"top":"var:preset|spacing|30"}}}} -->
				<p class="has-slate-500-color has-text-color has-small-font-size" style="margin-top:var(--wp--preset--spacing--30)">Para empresas en crecimiento con múltiples tiendas.</p>
				<!-- /wp:paragraph -->

				<!-- wp:separator {"backgroundColor":"slate-200","style":{"spacing":{"margin":{"top":"var:preset|spacing|50","bottom":"var:preset|spacing|50"}}}} -->
				<hr class="wp-block-separator has-text-color has-slate-200-color has-alpha-channel-opacity has-slate-200-background-color has-background" style="margin-top:var(--wp--preset--spacing--50);margin-bottom:var(--wp--preset--spacing--50)"/>
				<!-- /wp:separator -->

				<!-- wp:list {"style":{"typography":{"lineHeight":"2.2"}},"textColor":"slate-600","fontSize":"small","className":"is-style-no-bullets"} -->
				<ul style="line-height:2.2" class="is-style-no-bullets has-slate-600-color has-text-color has-small-font-size">
					<li>✓ 50 proveedores</li>
					<li>✓ 20 catálogos</li>
					<li>✓ 10 tiendas</li>
					<li>✓ Sincronización cada hora</li>
					<li>✓ Integración CRM</li>
					<li>✓ Soporte prioritario</li>
				</ul>
				<!-- /wp:list -->

				<!-- wp:buttons {"style":{"spacing":{"margin":{"top":"var:preset|spacing|50"}}}} -->
				<div class="wp-block-buttons" style="margin-top:var(--wp--preset--spacing--50)">
					<!-- wp:button {"width":100,"backgroundColor":"brand-600","style":{"border":{"radius":"0.5rem"}}} -->
					<div class="wp-block-button has-custom-width wp-block-button__width-100"><a class="wp-block-button__link has-brand-600-background-color has-background" style="border-radius:0.5rem">Elegir Professional</a></div>
					<!-- /wp:button -->
				</div>
				<!-- /wp:buttons -->

			</div>
			<!-- /wp:group -->
		</div>
		<!-- /wp:column -->

		<!-- wp:column -->
		<div class="wp-block-column">
			<!-- wp:group {"className":"syncstock-card","style":{"spacing":{"padding":{"top":"var:preset|spacing|70","bottom":"var:preset|spacing|70","left":"var:preset|spacing|60","right":"var:preset|spacing|60"}},"border":{"radius":"0.75rem"}},"backgroundColor":"white","layout":{"type":"constrained"}} -->
			<div class="wp-block-group syncstock-card has-white-background-color has-background" style="border-radius:0.75rem;padding-top:var(--wp--preset--spacing--70);padding-right:var(--wp--preset--spacing--60);padding-bottom:var(--wp--preset--spacing--70);padding-left:var(--wp--preset--spacing--60)">

				<!-- wp:heading {"level":3,"textColor":"slate-700","fontSize":"x-large"} -->
				<h3 class="wp-block-heading has-slate-700-color has-text-color has-x-large-font-size">Enterprise</h3>
				<!-- /wp:heading -->

				<!-- wp:group {"layout":{"type":"flex","flexWrap":"nowrap","verticalAlignment":"bottom"}} -->
				<div class="wp-block-group">
					<!-- wp:paragraph {"style":{"typography":{"fontWeight":"800","lineHeight":"1"}},"fontSize":"4x-large","fontFamily":"heading"} -->
					<p class="has-heading-font-family has-4-x-large-font-size" style="font-weight:800;line-height:1">199€</p>
					<!-- /wp:paragraph -->
					<!-- wp:paragraph {"textColor":"slate-400","fontSize":"small"} -->
					<p class="has-slate-400-color has-text-color has-small-font-size">/mes</p>
					<!-- /wp:paragraph -->
				</div>
				<!-- /wp:group -->

				<!-- wp:paragraph {"textColor":"slate-500","fontSize":"small","style":{"spacing":{"margin":{"top":"var:preset|spacing|30"}}}} -->
				<p class="has-slate-500-color has-text-color has-small-font-size" style="margin-top:var(--wp--preset--spacing--30)">Para grandes empresas con necesidades avanzadas.</p>
				<!-- /wp:paragraph -->

				<!-- wp:separator {"backgroundColor":"slate-200","style":{"spacing":{"margin":{"top":"var:preset|spacing|50","bottom":"var:preset|spacing|50"}}}} -->
				<hr class="wp-block-separator has-text-color has-slate-200-color has-alpha-channel-opacity has-slate-200-background-color has-background" style="margin-top:var(--wp--preset--spacing--50);margin-bottom:var(--wp--preset--spacing--50)"/>
				<!-- /wp:separator -->

				<!-- wp:list {"style":{"typography":{"lineHeight":"2.2"}},"textColor":"slate-600","fontSize":"small","className":"is-style-no-bullets"} -->
				<ul style="line-height:2.2" class="is-style-no-bullets has-slate-600-color has-text-color has-small-font-size">
					<li>✓ Proveedores ilimitados</li>
					<li>✓ Catálogos ilimitados</li>
					<li>✓ Tiendas ilimitadas</li>
					<li>✓ Sincronización en tiempo real</li>
					<li>✓ API personalizada</li>
					<li>✓ Soporte dedicado 24/7</li>
				</ul>
				<!-- /wp:list -->

				<!-- wp:buttons {"style":{"spacing":{"margin":{"top":"var:preset|spacing|50"}}}} -->
				<div class="wp-block-buttons" style="margin-top:var(--wp--preset--spacing--50)">
					<!-- wp:button {"width":100,"className":"is-style-outline","style":{"border":{"radius":"0.5rem"}}} -->
					<div class="wp-block-button has-custom-width wp-block-button__width-100 is-style-outline"><a class="wp-block-button__link" style="border-radius:0.5rem">Contactar Ventas</a></div>
					<!-- /wp:button -->
				</div>
				<!-- /wp:buttons -->

			</div>
			<!-- /wp:group -->
		</div>
		<!-- /wp:column -->

	</div>
	<!-- /wp:columns -->

</div>
<!-- /wp:group -->
