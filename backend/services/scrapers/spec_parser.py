"""
Parser de especificaciones técnicas IT.
Extrae CPU, RAM, GPU, SSD/HDD de nombres de producto de forma estructurada.
Diseñado para matching de alta precisión en el sector IT/electrónica.
"""
import logging
import re
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ProductSpecs:
    """Especificaciones técnicas extraídas de un nombre de producto."""
    # CPU
    cpu_brand: str | None = None       # "Intel", "AMD"
    cpu_family: str | None = None      # "Core i7", "Ryzen 7", "Xeon"
    cpu_model: str | None = None       # "13700K", "5800X3D"
    cpu_generation: int | None = None  # 13 (Intel gen 13), 5 (Ryzen 5xxx)

    # RAM
    ram_gb: int | None = None          # 16
    ram_type: str | None = None        # "DDR4", "DDR5", "LPDDR5"
    ram_speed_mhz: int | None = None   # 3200, 6000

    # GPU
    gpu_brand: str | None = None       # "NVIDIA", "AMD", "Intel"
    gpu_family: str | None = None      # "RTX", "RX", "Arc"
    gpu_model: str | None = None       # "4090", "7900 XT"
    gpu_vram_gb: int | None = None     # 24

    # Almacenamiento
    storage_gb: int | None = None      # 1000 (para 1TB)
    storage_type: str | None = None    # "NVMe", "SATA", "HDD"
    storage_interface: str | None = None  # "M.2", "2.5"", PCIe"

    # Otros
    form_factor: str | None = None     # "Mini-ITX", "ATX", "Micro-ATX"
    socket: str | None = None          # "LGA1700", "AM5", "LGA4677"

    # Metadata
    raw_specs: list[str] = field(default_factory=list)  # Especificaciones detectadas en bruto

    def has_specs(self) -> bool:
        """True si se extrajo al menos una especificación relevante."""
        return any([
            self.cpu_model, self.cpu_family,
            self.ram_gb,
            self.gpu_model, self.gpu_family,
            self.storage_gb,
        ])

    def to_dict(self) -> dict:
        return {
            "cpu_brand": self.cpu_brand,
            "cpu_family": self.cpu_family,
            "cpu_model": self.cpu_model,
            "cpu_generation": self.cpu_generation,
            "ram_gb": self.ram_gb,
            "ram_type": self.ram_type,
            "ram_speed_mhz": self.ram_speed_mhz,
            "gpu_brand": self.gpu_brand,
            "gpu_family": self.gpu_family,
            "gpu_model": self.gpu_model,
            "gpu_vram_gb": self.gpu_vram_gb,
            "storage_gb": self.storage_gb,
            "storage_type": self.storage_type,
            "storage_interface": self.storage_interface,
        }


class SpecParser:
    """
    Extrae especificaciones técnicas IT de nombres de producto.

    Soporta:
    - Intel: Core i3/i5/i7/i9, Xeon, Atom, Pentium, Celeron
    - AMD: Ryzen 3/5/7/9, EPYC, Athlon, Threadripper
    - NVIDIA: RTX 3xxx/4xxx/5xxx, GTX, Quadro, Tesla
    - AMD GPU: RX 6xxx/7xxx, Radeon, Instinct
    - Intel GPU: Arc A/B series
    - RAM: DDR3/4/5, LPDDR4/5, SO-DIMM
    - Storage: NVMe, SATA SSD, HDD con capacidades y factores de forma
    """

    # ── CPU Patterns ──────────────────────────────────────────────────────────

    _CPU_INTEL_PATTERNS = [
        # Core Ultra (gen 14+)
        (r'\bcore\s+ultra\s+([579])\s+(\d{3}[A-Z0-9]*)', 'Core Ultra', 'Intel'),
        # Core i3/i5/i7/i9 con modelo
        (r'\bcore\s+(i[3579])[- ](\d{4,5}[A-Z0-9]*)', 'Core {family}', 'Intel'),
        # Core i3/i5/i7/i9 sin modelo explícito
        (r'\b(i[3579])[- ](\d{4,5}[A-Z0-9]*)', 'Core {family}', 'Intel'),
        # Xeon
        (r'\bxeon\s+([A-Z]\d{4}[A-Z0-9]*)', 'Xeon', 'Intel'),
        (r'\bxeon\s+(gold|silver|bronze|platinum)\s+(\d{4}[A-Z]?)', 'Xeon {family}', 'Intel'),
        # Pentium/Celeron/Atom
        (r'\b(pentium|celeron|atom)\s+([A-Z0-9]+\d+[A-Z0-9]*)', '{family}', 'Intel'),
    ]

    _CPU_AMD_PATTERNS = [
        # Ryzen con modelo
        (r'\bryzen\s+([3579])\s+(\d{4}[A-Z0-9]*)', 'Ryzen {family}', 'AMD'),
        (r'\bryzen\s+(threadripper)\s+(\d{4}[A-Z0-9]*)', 'Threadripper', 'AMD'),
        (r'\bryzen\s+(threadripper\s+pro)\s+(\d{4}[A-Z0-9]*)', 'Threadripper Pro', 'AMD'),
        # EPYC
        (r'\bepyc\s+(\d{4}[A-Z0-9]*)', 'EPYC', 'AMD'),
        # Athlon
        (r'\bathlon\s+([A-Z0-9]+)', 'Athlon', 'AMD'),
        # FX
        (r'\bfx[- ](\d{4})', 'FX', 'AMD'),
    ]

    # ── GPU Patterns ──────────────────────────────────────────────────────────

    _GPU_NVIDIA_PATTERNS = [
        # RTX 4090/3090/2080 etc.
        (r'\brtx\s+(4090|4080\s*(?:super|ti)?|4070\s*(?:super|ti(?:\s+super)?)?|4060\s*(?:ti)?|3090\s*(?:ti)?|3080\s*(?:ti)?|3070\s*(?:ti)?|3060\s*(?:ti)?|2080\s*(?:super|ti)?|2070\s*(?:super)?|2060\s*(?:super)?|5090|5080|5070|5060)', 'RTX', 'NVIDIA'),
        # GTX
        (r'\bgtx\s+(\d{3,4}\s*(?:ti|super)?)', 'GTX', 'NVIDIA'),
        # Quadro
        (r'\bquadro\s+(rtx\s+)?\w+', 'Quadro', 'NVIDIA'),
        # Tesla/A-series datacenter
        (r'\btesla\s+([A-Z]\d+)', 'Tesla', 'NVIDIA'),
        (r'\b(a\d{2,4}(?:gb)?)\b(?=.*\bnvidia\b|\bgeforce\b)', 'A-series', 'NVIDIA'),
    ]

    _GPU_AMD_PATTERNS = [
        # RX 7900/6900/7800 etc.
        (r'\brx\s+(7900\s*(?:xtx|xt)?|7800\s*(?:xt)?|7700\s*(?:xt)?|7600\s*(?:xt)?|6950\s*(?:xt)?|6900\s*(?:xt)?|6800\s*(?:xt)?|6700\s*(?:xt)?|6600\s*(?:xt)?|9070\s*(?:xt)?|9060\s*(?:xt)?)', 'RX', 'AMD'),
        # Radeon pro
        (r'\bradeon\s+pro\s+([A-Z0-9]+)', 'Radeon Pro', 'AMD'),
        # Instinct
        (r'\binstinct\s+([A-Z0-9]+)', 'Instinct', 'AMD'),
        # Vega
        (r'\bvega\s+(\d+)', 'Vega', 'AMD'),
    ]

    _GPU_INTEL_PATTERNS = [
        # Arc A-series/B-series
        (r'\barc\s+(a[37][57]0[m]?)', 'Arc', 'Intel'),
        (r'\barc\s+(b[57]80[m]?)', 'Arc B', 'Intel'),
    ]

    # ── RAM Patterns ──────────────────────────────────────────────────────────

    _RAM_CAPACITY_PATTERN = r'(\d+)\s*(?:x\s*\d+\s*)?gb\b'
    _RAM_TYPE_PATTERN = r'\b(ddr[345]|lpddr[45]x?|so-dimm|dimm)\b'
    _RAM_SPEED_PATTERN = r'\b(\d{4,5})\s*mhz\b'
    # Atajos: "3200" solo como velocidad RAM cuando hay contexto DDR
    _RAM_SPEED_CONTEXT = r'\bddr[345][- _](\d{4,5})\b'

    # ── Storage Patterns ──────────────────────────────────────────────────────

    _STORAGE_CAPACITY_TB = r'(\d+(?:\.\d+)?)\s*tb\b'
    _STORAGE_CAPACITY_GB = r'(\d+)\s*gb\b'
    # Tipos de almacenamiento
    _STORAGE_TYPE_PATTERN = r'\b(nvme|pcie|sata|ssd|hdd|m\.?2|2\.5"\s*|3\.5"\s*|u\.?2)\b'
    # Marcas conocidas de SSD
    _SSD_BRANDS = {'samsung', 'wd', 'seagate', 'kingston', 'crucial', 'corsair', 'toshiba',
                   'micron', 'sk hynix', 'kioxia', 'transcend', 'lexar', 'pny', 'silicon power'}

    # ── Form Factor / Socket ──────────────────────────────────────────────────

    _SOCKET_PATTERN = r'\b(lga\d{3,4}|am[345]|fm[12]|tr4|sp3|sp5|lga4677|bga\d+)\b'
    _FORM_FACTOR_PATTERN = r'\b(mini[- ]itx|micro[- ]atx|e[- ]atx|atx|itx|mxm|u[- ]atx)\b'

    def parse(self, text: str) -> ProductSpecs:
        """
        Extrae especificaciones del texto del nombre de producto.

        Args:
            text: Nombre del producto (ej: "ASUS RTX 4090 OC 24GB")

        Returns:
            ProductSpecs con las especificaciones encontradas.
        """
        if not text:
            return ProductSpecs()

        specs = ProductSpecs()
        normalized = text.lower().strip()
        raw = []

        # CPU
        self._extract_cpu(normalized, specs, raw)
        # GPU
        self._extract_gpu(normalized, specs, raw)
        # RAM
        self._extract_ram(normalized, specs, raw)
        # Storage
        self._extract_storage(normalized, specs, raw)
        # Socket / Form factor
        self._extract_socket(normalized, specs)

        specs.raw_specs = raw
        return specs

    def _extract_cpu(self, text: str, specs: ProductSpecs, raw: list[str]) -> None:
        """Extrae información de CPU."""
        # Intel patterns
        for pattern, family_tpl, brand in self._CPU_INTEL_PATTERNS:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                groups = m.groups()
                family_letter = groups[0] if groups else ""
                model = groups[1] if len(groups) > 1 else groups[0] if groups else ""

                # Determinar family
                if "Ultra" in family_tpl:
                    specs.cpu_family = f"Core Ultra {family_letter}"
                elif "{family}" in family_tpl:
                    specs.cpu_family = f"Core {family_letter.upper()}"
                else:
                    specs.cpu_family = family_tpl

                specs.cpu_brand = brand
                specs.cpu_model = model.upper().strip()

                # Extraer generación de Intel
                if specs.cpu_model:
                    gen_match = re.match(r'(\d{2})\d{3}', specs.cpu_model)
                    if gen_match:
                        specs.cpu_generation = int(gen_match.group(1))
                    elif re.match(r'(\d{4})', specs.cpu_model):
                        first_digit = int(specs.cpu_model[0])
                        specs.cpu_generation = first_digit  # Gen aproximada

                raw.append(f"CPU: {specs.cpu_brand} {specs.cpu_family} {specs.cpu_model}")
                return

        # AMD patterns
        for pattern, family_tpl, brand in self._CPU_AMD_PATTERNS:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                groups = m.groups()
                if len(groups) >= 2:
                    family_num = groups[0]
                    model = groups[1].upper().strip()
                elif groups:
                    family_num = ""
                    model = groups[0].upper().strip()
                else:
                    continue

                if "{family}" in family_tpl:
                    specs.cpu_family = f"Ryzen {family_num}"
                else:
                    specs.cpu_family = family_tpl

                specs.cpu_brand = brand
                specs.cpu_model = model

                # Generación AMD: primer dígito del modelo Ryzen
                if specs.cpu_model and re.match(r'\d{4}', specs.cpu_model):
                    specs.cpu_generation = int(specs.cpu_model[0])

                raw.append(f"CPU: {specs.cpu_brand} {specs.cpu_family} {specs.cpu_model}")
                return

    def _extract_gpu(self, text: str, specs: ProductSpecs, raw: list[str]) -> None:
        """Extrae información de GPU."""
        for pattern, family, brand in self._GPU_NVIDIA_PATTERNS:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                specs.gpu_brand = brand
                specs.gpu_family = family
                specs.gpu_model = m.group(1).upper().strip()
                raw.append(f"GPU: {brand} {family} {specs.gpu_model}")
                # Extraer VRAM
                self._extract_vram(text, specs)
                return

        for pattern, family, brand in self._GPU_AMD_PATTERNS:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                specs.gpu_brand = brand
                specs.gpu_family = family
                specs.gpu_model = m.group(1).upper().strip()
                raw.append(f"GPU: {brand} {family} {specs.gpu_model}")
                self._extract_vram(text, specs)
                return

        for pattern, family, brand in self._GPU_INTEL_PATTERNS:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                specs.gpu_brand = brand
                specs.gpu_family = family
                specs.gpu_model = m.group(1).upper()
                raw.append(f"GPU: {brand} {family} {specs.gpu_model}")
                return

    def _extract_vram(self, text: str, specs: ProductSpecs) -> None:
        """Extrae VRAM de GPU (12GB, 16GB, 24GB...)."""
        # Patrones específicos de VRAM: "24GB GDDR6X", "16 GB VRAM"
        vram_patterns = [
            r'(\d+)\s*gb\s+(?:gddr[5-9]x?|hbm\d*|vram)',
            r'(\d+)\s*gb\s+(?:video|graphic)',
        ]
        for p in vram_patterns:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                specs.gpu_vram_gb = int(m.group(1))
                return
        # Fallback: GB solitario si solo hay una ocurrencia grande
        gb_matches = re.findall(r'(\d+)\s*gb', text, re.IGNORECASE)
        gpu_typical = {8, 10, 12, 16, 20, 24, 32, 48, 80}
        for gb_str in gb_matches:
            gb = int(gb_str)
            if gb in gpu_typical:
                specs.gpu_vram_gb = gb
                return

    def _extract_ram(self, text: str, specs: ProductSpecs, raw: list[str]) -> None:
        """Extrae capacidad, tipo y velocidad de RAM."""
        # Tipo DDR primero
        type_m = re.search(self._RAM_TYPE_PATTERN, text, re.IGNORECASE)
        if type_m:
            specs.ram_type = type_m.group(1).upper()

        # Velocidad con contexto DDR
        speed_ctx = re.search(self._RAM_SPEED_CONTEXT, text, re.IGNORECASE)
        if speed_ctx:
            specs.ram_speed_mhz = int(speed_ctx.group(1))
        else:
            speed_m = re.search(self._RAM_SPEED_PATTERN, text, re.IGNORECASE)
            if speed_m:
                specs.ram_speed_mhz = int(speed_m.group(1))

        # Capacidad: solo si hay contexto RAM
        if specs.ram_type or specs.ram_speed_mhz:
            cap_m = re.search(self._RAM_CAPACITY_PATTERN, text, re.IGNORECASE)
            if cap_m:
                # Evitar confusión con VRAM o almacenamiento
                gb_val = int(cap_m.group(1))
                ram_typical = {2, 4, 8, 12, 16, 24, 32, 48, 64, 96, 128, 192, 256}
                if gb_val in ram_typical:
                    specs.ram_gb = gb_val
                    raw.append(f"RAM: {specs.ram_gb}GB {specs.ram_type or ''} {specs.ram_speed_mhz or ''}MHz".strip())

    def _extract_storage(self, text: str, specs: ProductSpecs, raw: list[str]) -> None:
        """Extrae capacidad y tipo de almacenamiento."""
        # Tipo de almacenamiento
        type_m = re.search(self._STORAGE_TYPE_PATTERN, text, re.IGNORECASE)
        if type_m:
            t = type_m.group(1).lower()
            if t in ('nvme', 'pcie'):
                specs.storage_type = "NVMe"
            elif t == 'sata':
                specs.storage_type = "SATA"
            elif t == 'ssd':
                specs.storage_type = "SSD"
            elif t == 'hdd':
                specs.storage_type = "HDD"
            elif t in ('m.2', 'm2'):
                specs.storage_interface = "M.2"
            elif '2.5' in t:
                specs.storage_interface = '2.5"'
            elif '3.5' in t:
                specs.storage_interface = '3.5"'

        # Capacidad en TB (prioridad)
        tb_m = re.search(self._STORAGE_CAPACITY_TB, text, re.IGNORECASE)
        if tb_m:
            tb_val = float(tb_m.group(1))
            specs.storage_gb = int(tb_val * 1000)
            raw.append(f"Storage: {tb_val}TB {specs.storage_type or ''}")
            return

        # Capacidad en GB (solo si parece almacenamiento)
        if specs.storage_type or specs.storage_interface:
            gb_m = re.search(self._STORAGE_CAPACITY_GB, text, re.IGNORECASE)
            if gb_m:
                gb_val = int(gb_m.group(1))
                storage_typical = {120, 128, 240, 256, 480, 500, 512, 960, 1000, 1024, 2000, 2048, 4000, 4096}
                # Tolerancia: múltiplos de 120/128
                if gb_val in storage_typical or (gb_val > 100 and gb_val % 8 == 0):
                    specs.storage_gb = gb_val
                    raw.append(f"Storage: {gb_val}GB {specs.storage_type or ''}")

    def _extract_socket(self, text: str, specs: ProductSpecs) -> None:
        """Extrae socket y factor de forma."""
        socket_m = re.search(self._SOCKET_PATTERN, text, re.IGNORECASE)
        if socket_m:
            specs.socket = socket_m.group(1).upper()

        ff_m = re.search(self._FORM_FACTOR_PATTERN, text, re.IGNORECASE)
        if ff_m:
            specs.form_factor = ff_m.group(1).title()


# Instancia global singleton
spec_parser = SpecParser()
