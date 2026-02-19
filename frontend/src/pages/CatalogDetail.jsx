import { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api } from "../App";
import { toast } from "sonner";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Checkbox } from "../components/ui/checkbox";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../components/ui/table";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "../components/ui/alert-dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import {
  BookOpen,
  ArrowLeft,
  Search,
  Package,
  Trash2,
  RefreshCw,
  Plus,
  DollarSign,
  AlertTriangle,
  Percent,
  Filter
} from "lucide-react";

const CatalogDetail = () => {
  const { catalogId } = useParams();
  const navigate = useNavigate();
  
  const [catalog, setCatalog] = useState(null);
  const [products, setProducts] = useState([]);
  const [allProducts, setAllProducts] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selectedIds, setSelectedIds] = useState([]);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [addSearch, setAddSearch] = useState("");
  const [addSupplierFilter, setAddSupplierFilter] = useState("all");
  const [selectedToAdd, setSelectedToAdd] = useState([]);
  const [adding, setAdding] = useState(false);

  const fetchCatalog = useCallback(async () => {
    try {
      const res = await api.get(`/catalogs/${catalogId}`);
      setCatalog(res.data);
    } catch (error) {
      toast.error("Error al cargar el catálogo");
      navigate("/catalogs");
    }
  }, [catalogId, navigate]);

  const fetchProducts = useCallback(async () => {
    try {
      const res = await api.get(`/catalogs/${catalogId}/products?search=${search}`);
      setProducts(res.data);
    } catch (error) {
      toast.error("Error al cargar productos");
    }
  }, [catalogId, search]);

  const fetchAllProducts = useCallback(async () => {
    try {
      const [productsRes, suppliersRes] = await Promise.all([
        api.get("/products?limit=500"),
        api.get("/suppliers")
      ]);
      setAllProducts(productsRes.data);
      setSuppliers(suppliersRes.data);
    } catch (error) {
      console.error("Error fetching products:", error);
    }
  }, []);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([fetchCatalog(), fetchProducts(), fetchAllProducts()]);
      setLoading(false);
    };
    loadData();
  }, [fetchCatalog, fetchProducts, fetchAllProducts]);

  // Get products not in catalog
  const productsNotInCatalog = allProducts.filter(
    p => !products.some(cp => cp.product_id === p.id)
  ).filter(p => {
    const matchesSearch = addSearch === "" || 
      p.name.toLowerCase().includes(addSearch.toLowerCase()) ||
      p.sku.toLowerCase().includes(addSearch.toLowerCase());
    const matchesSupplier = addSupplierFilter === "all" || p.supplier_id === addSupplierFilter;
    return matchesSearch && matchesSupplier;
  });

  const handleSelectAll = (checked) => {
    if (checked) {
      setSelectedIds(products.map(p => p.id));
    } else {
      setSelectedIds([]);
    }
  };

  const handleSelectOne = (id, checked) => {
    if (checked) {
      setSelectedIds([...selectedIds, id]);
    } else {
      setSelectedIds(selectedIds.filter(i => i !== id));
    }
  };

  const handleRemoveSelected = async () => {
    try {
      await Promise.all(
        selectedIds.map(id => api.delete(`/catalogs/${catalogId}/products/${id}`))
      );
      toast.success(`${selectedIds.length} productos eliminados del catálogo`);
      setSelectedIds([]);
      setShowDeleteDialog(false);
      fetchProducts();
      fetchCatalog();
    } catch (error) {
      toast.error("Error al eliminar productos");
    }
  };

  const handleAddProducts = async () => {
    if (selectedToAdd.length === 0) {
      toast.error("Selecciona al menos un producto");
      return;
    }
    
    setAdding(true);
    try {
      await api.post(`/catalogs/${catalogId}/products`, {
        product_ids: selectedToAdd
      });
      toast.success(`${selectedToAdd.length} productos añadidos al catálogo`);
      setSelectedToAdd([]);
      setShowAddDialog(false);
      fetchProducts();
      fetchCatalog();
    } catch (error) {
      toast.error("Error al añadir productos");
    } finally {
      setAdding(false);
    }
  };

  const handleSelectAllToAdd = (checked) => {
    if (checked) {
      setSelectedToAdd(productsNotInCatalog.map(p => p.id));
    } else {
      setSelectedToAdd([]);
    }
  };

  if (loading) {
    return (
      <div className="p-6 lg:p-8 flex items-center justify-center min-h-[50vh]">
        <RefreshCw className="w-8 h-8 animate-spin text-indigo-600" />
      </div>
    );
  }

  if (!catalog) {
    return null;
  }

  // Stats
  const totalProducts = products.length;
  const totalValue = products.reduce((sum, p) => sum + (p.final_price || 0), 0);
  const lowStock = products.filter(p => p.product?.stock <= 5 && p.product?.stock > 0).length;
  const outOfStock = products.filter(p => p.product?.stock === 0).length;

  return (
    <div className="p-6 lg:p-8 animate-fade-in">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div className="flex items-center gap-4">
          <Button 
            variant="ghost" 
            size="icon"
            onClick={() => navigate("/catalogs")}
            className="hover:bg-slate-100"
          >
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <div>
            <div className="flex items-center gap-2 mb-1">
              <h1 className="text-2xl font-bold text-slate-900" style={{ fontFamily: 'Manrope, sans-serif' }}>
                {catalog.name}
              </h1>
              {catalog.is_default && (
                <Badge className="bg-indigo-100 text-indigo-700 border-0">
                  Por defecto
                </Badge>
              )}
            </div>
            {catalog.description && (
              <p className="text-slate-500 text-sm">{catalog.description}</p>
            )}
          </div>
        </div>
        <div className="flex gap-2">
          {selectedIds.length > 0 && (
            <Button 
              variant="outline"
              onClick={() => setShowDeleteDialog(true)}
              className="text-rose-600 border-rose-200 hover:bg-rose-50"
            >
              <Trash2 className="w-4 h-4 mr-2" />
              Eliminar ({selectedIds.length})
            </Button>
          )}
          <Button 
            onClick={() => { setSelectedToAdd([]); setShowAddDialog(true); }} 
            className="btn-primary"
            data-testid="add-products-btn"
          >
            <Plus className="w-4 h-4 mr-2" strokeWidth={1.5} />
            Añadir Productos
          </Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <Card className="border-slate-200">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Productos</p>
                <p className="text-2xl font-bold text-slate-900">{totalProducts}</p>
              </div>
              <Package className="w-8 h-8 text-indigo-200" strokeWidth={1.5} />
            </div>
          </CardContent>
        </Card>
        <Card className="border-emerald-200 bg-emerald-50">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-emerald-600">Valor Total</p>
                <p className="text-2xl font-bold text-emerald-700">
                  {totalValue.toLocaleString('es-ES', { style: 'currency', currency: 'EUR' })}
                </p>
              </div>
              <DollarSign className="w-8 h-8 text-emerald-200" strokeWidth={1.5} />
            </div>
          </CardContent>
        </Card>
        <Card className="border-amber-200 bg-amber-50">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-amber-600">Stock Bajo</p>
                <p className="text-2xl font-bold text-amber-700">{lowStock}</p>
              </div>
              <AlertTriangle className="w-8 h-8 text-amber-200" strokeWidth={1.5} />
            </div>
          </CardContent>
        </Card>
        <Card className="border-rose-200 bg-rose-50">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-rose-600">Sin Stock</p>
                <p className="text-2xl font-bold text-rose-700">{outOfStock}</p>
              </div>
              <Package className="w-8 h-8 text-rose-200" strokeWidth={1.5} />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Search */}
      <div className="mb-4">
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <Input
            placeholder="Buscar por nombre o SKU..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="input-base pl-9"
            data-testid="search-catalog-products"
          />
        </div>
      </div>

      {/* Products Table */}
      {products.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">
            <Package className="w-10 h-10" strokeWidth={1.5} />
          </div>
          <h3 className="text-lg font-semibold text-slate-900 mb-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
            {search ? "No se encontraron productos" : "Este catálogo está vacío"}
          </h3>
          <p className="text-slate-500 mb-4">
            {search ? "Prueba con otros términos de búsqueda" : "Añade productos desde tu inventario para comenzar"}
          </p>
          {!search && (
            <Button onClick={() => setShowAddDialog(true)} className="btn-primary">
              <Plus className="w-4 h-4 mr-2" strokeWidth={1.5} />
              Añadir Productos
            </Button>
          )}
        </div>
      ) : (
        <Card className="border-slate-200">
          <CardContent className="p-0 overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow className="table-header">
                  <TableHead className="w-[50px]">
                    <Checkbox
                      checked={selectedIds.length === products.length && products.length > 0}
                      onCheckedChange={handleSelectAll}
                    />
                  </TableHead>
                  <TableHead>Producto</TableHead>
                  <TableHead>SKU</TableHead>
                  <TableHead>Proveedor</TableHead>
                  <TableHead className="text-right">Precio Base</TableHead>
                  <TableHead className="text-right">Precio Final</TableHead>
                  <TableHead className="text-right">Stock</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {products.map((item) => (
                  <TableRow key={item.id} className="table-row" data-testid={`catalog-product-${item.id}`}>
                    <TableCell>
                      <Checkbox
                        checked={selectedIds.includes(item.id)}
                        onCheckedChange={(checked) => handleSelectOne(item.id, checked)}
                      />
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-slate-100 rounded-lg flex items-center justify-center">
                          {item.product?.image_url ? (
                            <img 
                              src={item.product.image_url} 
                              alt="" 
                              className="w-10 h-10 object-cover rounded-lg"
                            />
                          ) : (
                            <Package className="w-5 h-5 text-slate-400" />
                          )}
                        </div>
                        <div>
                          <p className="font-medium text-slate-900 line-clamp-1">
                            {item.custom_name || item.product?.name}
                          </p>
                          <p className="text-xs text-slate-500">{item.product?.category || "Sin categoría"}</p>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="font-mono text-sm">{item.product?.sku}</TableCell>
                    <TableCell className="text-sm text-slate-600">{item.product?.supplier_name}</TableCell>
                    <TableCell className="text-right">
                      {(item.custom_price || item.product?.price || 0).toLocaleString('es-ES', { style: 'currency', currency: 'EUR' })}
                    </TableCell>
                    <TableCell className="text-right font-medium text-emerald-600">
                      {(item.final_price || 0).toLocaleString('es-ES', { style: 'currency', currency: 'EUR' })}
                    </TableCell>
                    <TableCell className="text-right">
                      {item.product?.stock === 0 ? (
                        <Badge className="bg-rose-100 text-rose-700 border-0">Sin stock</Badge>
                      ) : item.product?.stock <= 5 ? (
                        <Badge className="bg-amber-100 text-amber-700 border-0">{item.product?.stock}</Badge>
                      ) : (
                        <span className="text-slate-900">{item.product?.stock}</span>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle style={{ fontFamily: 'Manrope, sans-serif' }}>
              ¿Eliminar productos del catálogo?
            </AlertDialogTitle>
            <AlertDialogDescription>
              Se eliminarán {selectedIds.length} productos del catálogo "{catalog.name}". 
              Los productos seguirán disponibles en tu inventario.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="btn-secondary">Cancelar</AlertDialogCancel>
            <AlertDialogAction onClick={handleRemoveSelected} className="bg-rose-600 hover:bg-rose-700 text-white">
              Eliminar del catálogo
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Add Products Dialog */}
      <AlertDialog open={showAddDialog} onOpenChange={setShowAddDialog}>
        <AlertDialogContent className="max-w-3xl max-h-[85vh] overflow-hidden flex flex-col">
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
              <Plus className="w-5 h-5 text-indigo-600" />
              Añadir Productos al Catálogo
            </AlertDialogTitle>
            <AlertDialogDescription>
              Selecciona los productos que quieres añadir a "{catalog.name}"
            </AlertDialogDescription>
          </AlertDialogHeader>
          
          {/* Filters */}
          <div className="flex gap-3 py-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <Input
                placeholder="Buscar productos..."
                value={addSearch}
                onChange={(e) => setAddSearch(e.target.value)}
                className="input-base pl-9"
              />
            </div>
            <Select value={addSupplierFilter} onValueChange={setAddSupplierFilter}>
              <SelectTrigger className="w-[200px] input-base">
                <Filter className="w-4 h-4 mr-2 text-slate-400" />
                <SelectValue placeholder="Proveedor" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todos los proveedores</SelectItem>
                {suppliers.map(s => (
                  <SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          
          {/* Products List */}
          <div className="flex-1 overflow-y-auto border rounded-lg max-h-[400px]">
            {productsNotInCatalog.length === 0 ? (
              <div className="p-8 text-center text-slate-500">
                <Package className="w-10 h-10 mx-auto mb-2 text-slate-300" />
                <p>No hay productos disponibles para añadir</p>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow className="table-header sticky top-0 bg-slate-50 z-10">
                    <TableHead className="w-[50px]">
                      <Checkbox
                        checked={selectedToAdd.length === productsNotInCatalog.length && productsNotInCatalog.length > 0}
                        onCheckedChange={handleSelectAllToAdd}
                      />
                    </TableHead>
                    <TableHead>Producto</TableHead>
                    <TableHead>Proveedor</TableHead>
                    <TableHead className="text-right">Precio</TableHead>
                    <TableHead className="text-right">Stock</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {productsNotInCatalog.slice(0, 100).map((product) => (
                    <TableRow key={product.id} className="table-row">
                      <TableCell>
                        <Checkbox
                          checked={selectedToAdd.includes(product.id)}
                          onCheckedChange={(checked) => {
                            if (checked) {
                              setSelectedToAdd([...selectedToAdd, product.id]);
                            } else {
                              setSelectedToAdd(selectedToAdd.filter(id => id !== product.id));
                            }
                          }}
                        />
                      </TableCell>
                      <TableCell>
                        <div>
                          <p className="font-medium text-slate-900 line-clamp-1">{product.name}</p>
                          <p className="text-xs text-slate-500 font-mono">{product.sku}</p>
                        </div>
                      </TableCell>
                      <TableCell className="text-sm text-slate-600">{product.supplier_name}</TableCell>
                      <TableCell className="text-right">
                        {product.price.toLocaleString('es-ES', { style: 'currency', currency: 'EUR' })}
                      </TableCell>
                      <TableCell className="text-right">{product.stock}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </div>
          
          {productsNotInCatalog.length > 100 && (
            <p className="text-xs text-slate-500 text-center py-2">
              Mostrando 100 de {productsNotInCatalog.length} productos. Usa el buscador para filtrar.
            </p>
          )}
          
          <AlertDialogFooter className="pt-4 border-t">
            <AlertDialogCancel className="btn-secondary">Cancelar</AlertDialogCancel>
            <Button 
              onClick={handleAddProducts} 
              disabled={adding || selectedToAdd.length === 0}
              className="btn-primary"
            >
              {adding ? (
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Plus className="w-4 h-4 mr-2" />
              )}
              Añadir {selectedToAdd.length > 0 ? `(${selectedToAdd.length})` : ''}
            </Button>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default CatalogDetail;
