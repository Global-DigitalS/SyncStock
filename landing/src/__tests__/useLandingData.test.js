import { renderHook, waitFor } from "@testing-library/react";
import { useLandingData } from "../hooks/useLandingData";
import * as landingApiService from "../services/landingApiService";
import {
  DEFAULT_BRANDING,
  DEFAULT_PAGES,
  DEFAULT_PLANS,
} from "../constants/defaultBranding";

// Mockear el servicio de API
jest.mock("../services/landingApiService");

describe("useLandingData", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("Carga de datos exitosa", () => {
    it("debería cargar branding y páginas correctamente", async () => {
      const mockBranding = {
        company_name: "Test Company",
        primary_color: "#123456",
      };
      const mockPages = [
        {
          id: "test-1",
          slug: "test-page",
          title: "Test Page",
          content: "Test content",
        },
      ];

      landingApiService.getBranding.mockResolvedValue(mockBranding);
      landingApiService.getPublicPages.mockResolvedValue(mockPages);

      const { result } = renderHook(() => useLandingData());

      // Inicialmente debe estar cargando
      expect(result.current.loading).toBe(true);

      // Esperar a que se carguen los datos
      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      // Verificar que los datos se hayan cargado correctamente
      expect(result.current.branding).toEqual({
        ...DEFAULT_BRANDING,
        ...mockBranding,
      });
      expect(result.current.pages).toEqual(mockPages);
      expect(result.current.error.brandingError).toBeNull();
      expect(result.current.error.pagesError).toBeNull();
    });

    it("debería mantener DEFAULT_PLANS sin cambios", async () => {
      landingApiService.getBranding.mockResolvedValue({});
      landingApiService.getPublicPages.mockResolvedValue([]);

      const { result } = renderHook(() => useLandingData());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.plans).toEqual(DEFAULT_PLANS);
    });

    it("debería proporcionar alias isLoading", async () => {
      landingApiService.getBranding.mockResolvedValue({});
      landingApiService.getPublicPages.mockResolvedValue([]);

      const { result } = renderHook(() => useLandingData());

      expect(result.current.isLoading).toBe(result.current.loading);

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });
    });
  });

  describe("Carga de página específica con slug", () => {
    it("debería cargar página específica cuando se proporciona slug", async () => {
      const mockPageData = {
        id: "about-page",
        slug: "acerca-de",
        title: "Acerca de Nosotros",
        content: "Contenido sobre nosotros",
        is_published: true,
      };

      landingApiService.getBranding.mockResolvedValue({});
      landingApiService.getPublicPages.mockResolvedValue([]);
      landingApiService.getPageBySlug.mockResolvedValue(mockPageData);

      const { result } = renderHook(() => useLandingData({ slug: "acerca-de" }));

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(landingApiService.getPageBySlug).toHaveBeenCalledWith("acerca-de");
      expect(result.current.currentPage).toEqual(mockPageData);
      expect(result.current.error.currentPageError).toBeNull();
    });

    it("debería cargar nueva página cuando slug cambia", async () => {
      const mockPage1 = { id: "1", slug: "page1", title: "Page 1" };
      const mockPage2 = { id: "2", slug: "page2", title: "Page 2" };

      landingApiService.getBranding.mockResolvedValue({});
      landingApiService.getPublicPages.mockResolvedValue([]);
      landingApiService.getPageBySlug.mockResolvedValueOnce(mockPage1);

      const { result, rerender } = renderHook(
        ({ slug }) => useLandingData({ slug }),
        { initialProps: { slug: "page1" } }
      );

      await waitFor(() => {
        expect(result.current.currentPage).toEqual(mockPage1);
      });

      // Cambiar slug
      landingApiService.getPageBySlug.mockResolvedValueOnce(mockPage2);

      rerender({ slug: "page2" });

      await waitFor(() => {
        expect(landingApiService.getPageBySlug).toHaveBeenCalledWith("page2");
        expect(result.current.currentPage).toEqual(mockPage2);
      });
    });

    it("debería limpiar currentPage cuando slug se elimina", async () => {
      const mockPageData = { id: "1", slug: "page1", title: "Page 1" };

      landingApiService.getBranding.mockResolvedValue({});
      landingApiService.getPublicPages.mockResolvedValue([]);
      landingApiService.getPageBySlug.mockResolvedValue(mockPageData);

      const { result, rerender } = renderHook(
        ({ slug }) => useLandingData({ slug }),
        { initialProps: { slug: "page1" } }
      );

      await waitFor(() => {
        expect(result.current.currentPage).toEqual(mockPageData);
      });

      // Remover slug
      rerender({ slug: null });

      await waitFor(() => {
        expect(result.current.currentPage).toBeNull();
      });
    });
  });

  describe("Manejo de errores", () => {
    it("debería usar defaults cuando getBranding falla", async () => {
      const error = new Error("Network error");
      landingApiService.getBranding.mockRejectedValue(error);
      landingApiService.getPublicPages.mockResolvedValue([]);

      const { result } = renderHook(() => useLandingData());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.branding).toEqual(DEFAULT_BRANDING);
      expect(result.current.error.brandingError).toEqual(error);
    });

    it("debería usar defaults cuando getPublicPages falla", async () => {
      const error = new Error("API error");
      landingApiService.getBranding.mockResolvedValue({});
      landingApiService.getPublicPages.mockRejectedValue(error);

      const { result } = renderHook(() => useLandingData());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.pages).toEqual(DEFAULT_PAGES);
      expect(result.current.error.pagesError).toEqual(error);
    });

    it("debería registrar error cuando falla getPageBySlug", async () => {
      const pageError = new Error("Page not found");
      landingApiService.getBranding.mockResolvedValue({});
      landingApiService.getPublicPages.mockResolvedValue([]);
      landingApiService.getPageBySlug.mockRejectedValue(pageError);

      const consoleSpy = jest.spyOn(console, "warn").mockImplementation();

      const { result } = renderHook(() => useLandingData({ slug: "missing" }));

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.currentPage).toBeNull();
      expect(result.current.error.currentPageError).toEqual(pageError);
      expect(consoleSpy).toHaveBeenCalled();

      consoleSpy.mockRestore();
    });

    it("debería manejar múltiples errores simultáneamente", async () => {
      const brandingError = new Error("Branding error");
      const pagesError = new Error("Pages error");

      landingApiService.getBranding.mockRejectedValue(brandingError);
      landingApiService.getPublicPages.mockRejectedValue(pagesError);

      const { result } = renderHook(() => useLandingData());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.error.brandingError).toEqual(brandingError);
      expect(result.current.error.pagesError).toEqual(pagesError);
      expect(result.current.branding).toEqual(DEFAULT_BRANDING);
      expect(result.current.pages).toEqual(DEFAULT_PAGES);
    });

    it("debería mantener valores previos cuando API retorna null/undefined", async () => {
      landingApiService.getBranding.mockResolvedValue(null);
      landingApiService.getPublicPages.mockResolvedValue(undefined);

      const { result } = renderHook(() => useLandingData());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      // Cuando la respuesta es null/undefined, mantiene los defaults
      expect(result.current.branding).toEqual(DEFAULT_BRANDING);
      expect(result.current.pages).toEqual(DEFAULT_PAGES);
    });
  });

  describe("Limpieza de unmount", () => {
    it("no debería actualizar estado si el componente se desmonta durante la carga", async () => {
      const consoleSpy = jest.spyOn(console, "error").mockImplementation();

      landingApiService.getBranding.mockImplementation(
        () =>
          new Promise((resolve) => {
            setTimeout(() => resolve({}), 100);
          })
      );
      landingApiService.getPublicPages.mockResolvedValue([]);

      const { unmount } = renderHook(() => useLandingData());

      // Desmontar inmediatamente
      unmount();

      // Esperar a que se resuelva la promesa
      await new Promise((resolve) => setTimeout(resolve, 150));

      // No debería haber errores de actualización en componente desmontado
      const updateWarnings = consoleSpy.mock.calls.filter((call) =>
        call[0]?.includes?.("isMounted")
      );
      expect(updateWarnings).toEqual([]);

      consoleSpy.mockRestore();
    });
  });

  describe("Parámetros opcionales", () => {
    it("debería usar valores por defecto cuando no se proporciona options", async () => {
      landingApiService.getBranding.mockResolvedValue({});
      landingApiService.getPublicPages.mockResolvedValue([]);

      const { result } = renderHook(() => useLandingData());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.currentPage).toBeNull();
      expect(landingApiService.getPageBySlug).not.toHaveBeenCalled();
    });

    it("debería usar valores por defecto cuando options es null", async () => {
      landingApiService.getBranding.mockResolvedValue({});
      landingApiService.getPublicPages.mockResolvedValue([]);

      const { result } = renderHook(() => useLandingData(null));

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.currentPage).toBeNull();
    });
  });

  describe("Fusión de branding", () => {
    it("debería fusionar respuesta de API con DEFAULT_BRANDING", async () => {
      const partialBranding = {
        company_name: "Mi Empresa",
        primary_color: "#FF0000",
      };

      landingApiService.getBranding.mockResolvedValue(partialBranding);
      landingApiService.getPublicPages.mockResolvedValue([]);

      const { result } = renderHook(() => useLandingData());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.branding).toEqual({
        ...DEFAULT_BRANDING,
        ...partialBranding,
      });
      expect(result.current.branding.company_name).toBe("Mi Empresa");
      expect(result.current.branding.primary_color).toBe("#FF0000");
      expect(result.current.branding.app_slogan).toBe(
        DEFAULT_BRANDING.app_slogan
      );
    });
  });

  describe("Promise.allSettled behavior", () => {
    it("debería manejar Promise.allSettled cuando una promesa se rechaza", async () => {
      landingApiService.getBranding.mockRejectedValue(
        new Error("Branding failed")
      );
      landingApiService.getPublicPages.mockResolvedValue([
        { id: "1", slug: "test" },
      ]);

      const { result } = renderHook(() => useLandingData());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      // El hook debe continuar incluso si una promesa falla
      expect(result.current.pages).toEqual([{ id: "1", slug: "test" }]);
      expect(result.current.error.brandingError).not.toBeNull();
    });
  });
});
