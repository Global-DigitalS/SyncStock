import { useState, useEffect } from "react";
import { toast } from "sonner";
import {
  User, Mail, Building2, Phone, Save, Edit2, X, Lock,
  FileText, MapPin, Globe, CreditCard, Crown, Sparkles, Calendar,
  LifeBuoy
} from "lucide-react";
import { useAuth, api } from "../App";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { Badge } from "../components/ui/badge";
import Support from "./Support";

const Profile = () => {
  const { user, refreshUser } = useAuth();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [editingPersonal, setEditingPersonal] = useState(false);
  const [editingBilling, setEditingBilling] = useState(false);
  const [editingPassword, setEditingPassword] = useState(false);
  
  const [personalData, setPersonalData] = useState({
    name: "",
    email: "",
    company: "",
    phone: ""
  });
  
  const [billingData, setBillingData] = useState({
    company_name: "",
    tax_id: "",
    address: "",
    city: "",
    postal_code: "",
    country: "España",
    billing_email: ""
  });
  
  const [passwordData, setPasswordData] = useState({
    current_password: "",
    new_password: "",
    confirm_password: ""
  });
  
  const [subscription, setSubscription] = useState(null);

  useEffect(() => {
    loadProfileData();
  }, []);

  const loadProfileData = async () => {
    setLoading(true);
    try {
      // Load user data
      const userRes = await api.get("/auth/me");
      if (userRes.data) {
        setPersonalData({
          name: userRes.data.name || "",
          email: userRes.data.email || "",
          company: userRes.data.company || "",
          phone: userRes.data.phone || ""
        });
      }
      
      // Load billing data
      try {
        const billingRes = await api.get("/subscriptions/billing-info");
        if (billingRes.data && Object.keys(billingRes.data).length > 0) {
          setBillingData({
            company_name: billingRes.data.company_name || "",
            tax_id: billingRes.data.tax_id || "",
            address: billingRes.data.address || "",
            city: billingRes.data.city || "",
            postal_code: billingRes.data.postal_code || "",
            country: billingRes.data.country || "España",
            billing_email: billingRes.data.billing_email || ""
          });
        }
      } catch (e) {
        // No billing info yet
      }
      
      // Load subscription data
      try {
        const subRes = await api.get("/subscriptions/my");
        setSubscription(subRes.data);
      } catch (e) {
        // No subscription
      }
    } catch (error) {
      toast.error("Error al cargar los datos del perfil");
    } finally {
      setLoading(false);
    }
  };

  const handlePersonalChange = (e) => {
    setPersonalData({ ...personalData, [e.target.name]: e.target.value });
  };

  const handleBillingChange = (e) => {
    setBillingData({ ...billingData, [e.target.name]: e.target.value });
  };

  const handlePasswordChange = (e) => {
    setPasswordData({ ...passwordData, [e.target.name]: e.target.value });
  };

  const savePersonalData = async () => {
    setSaving(true);
    try {
      await api.put("/auth/profile", {
        name: personalData.name,
        company: personalData.company,
        phone: personalData.phone
      });
      toast.success("Datos personales actualizados");
      setEditingPersonal(false);
      if (refreshUser) refreshUser();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al guardar los datos");
    } finally {
      setSaving(false);
    }
  };

  const saveBillingData = async () => {
    if (!billingData.company_name || !billingData.tax_id) {
      toast.error("Nombre y NIF/CIF son obligatorios");
      return;
    }
    
    setSaving(true);
    try {
      await api.post("/subscriptions/billing-info", billingData);
      toast.success("Datos de facturación actualizados");
      setEditingBilling(false);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al guardar los datos de facturación");
    } finally {
      setSaving(false);
    }
  };

  const changePassword = async () => {
    if (!passwordData.current_password || !passwordData.new_password) {
      toast.error("Completa todos los campos");
      return;
    }
    if (passwordData.new_password !== passwordData.confirm_password) {
      toast.error("Las contraseñas no coinciden");
      return;
    }
    if (passwordData.new_password.length < 6) {
      toast.error("La contraseña debe tener al menos 6 caracteres");
      return;
    }
    
    setSaving(true);
    try {
      await api.post("/auth/change-password", {
        current_password: passwordData.current_password,
        new_password: passwordData.new_password
      });
      toast.success("Contraseña actualizada correctamente");
      setEditingPassword(false);
      setPasswordData({ current_password: "", new_password: "", confirm_password: "" });
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al cambiar la contraseña");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="spinner w-8 h-8 border-3 border-indigo-200 border-t-indigo-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="profile-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900" style={{ fontFamily: 'Manrope, sans-serif' }}>
            Mi Perfil
          </h1>
          <p className="text-slate-500 mt-1">
            Gestiona tu información personal y de facturación
          </p>
        </div>
      </div>

      {/* Subscription Banner */}
      {subscription && (
        <Card className="bg-gradient-to-r from-indigo-500 to-purple-600 text-white border-0">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-white/20 rounded-lg flex items-center justify-center">
                  <Crown className="w-6 h-6" />
                </div>
                <div>
                  <p className="text-white/80 text-sm">Plan actual</p>
                  <p className="text-2xl font-bold">{subscription.plan?.name || "Free"}</p>
                </div>
              </div>
              <div className="text-right">
                {subscription.is_in_trial && (
                  <Badge className="bg-amber-500 text-white mb-2">
                    <Sparkles className="w-3 h-3 mr-1" />
                    Período de prueba
                  </Badge>
                )}
                {subscription.trial_days_left > 0 && (
                  <p className="text-white/80 text-sm flex items-center gap-1">
                    <Calendar className="w-4 h-4" />
                    {subscription.trial_days_left} días restantes
                  </p>
                )}
                {!subscription.is_free && subscription.subscription?.current_period_end && (
                  <p className="text-white/80 text-sm">
                    Próxima facturación: {new Date(subscription.subscription.current_period_end).toLocaleDateString('es-ES')}
                  </p>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <Tabs defaultValue="personal" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4 lg:w-[560px]">
          <TabsTrigger value="personal" data-testid="tab-personal">
            <User className="w-4 h-4 mr-2" />
            Personal
          </TabsTrigger>
          <TabsTrigger value="billing" data-testid="tab-billing">
            <FileText className="w-4 h-4 mr-2" />
            Facturación
          </TabsTrigger>
          <TabsTrigger value="security" data-testid="tab-security">
            <Lock className="w-4 h-4 mr-2" />
            Seguridad
          </TabsTrigger>
          <TabsTrigger value="support" data-testid="tab-support">
            <LifeBuoy className="w-4 h-4 mr-2" />
            Soporte
          </TabsTrigger>
        </TabsList>

        {/* Personal Data Tab */}
        <TabsContent value="personal">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Datos Personales</CardTitle>
                <CardDescription>Tu información de cuenta</CardDescription>
              </div>
              {!editingPersonal ? (
                <Button variant="outline" size="sm" onClick={() => setEditingPersonal(true)} data-testid="edit-personal-btn">
                  <Edit2 className="w-4 h-4 mr-2" />
                  Editar
                </Button>
              ) : (
                <Button variant="ghost" size="sm" onClick={() => setEditingPersonal(false)}>
                  <X className="w-4 h-4 mr-2" />
                  Cancelar
                </Button>
              )}
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Nombre completo</Label>
                  <div className="relative">
                    <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <Input
                      id="name"
                      name="name"
                      value={personalData.name}
                      onChange={handlePersonalChange}
                      disabled={!editingPersonal}
                      className="pl-10"
                      data-testid="input-name"
                    />
                  </div>
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="email">Correo electrónico</Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <Input
                      id="email"
                      name="email"
                      value={personalData.email}
                      disabled={true}
                      className="pl-10 bg-slate-50"
                      data-testid="input-email"
                    />
                  </div>
                  <p className="text-xs text-slate-500">El email no se puede modificar</p>
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="company">Empresa</Label>
                  <div className="relative">
                    <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <Input
                      id="company"
                      name="company"
                      value={personalData.company}
                      onChange={handlePersonalChange}
                      disabled={!editingPersonal}
                      placeholder="Nombre de tu empresa"
                      className="pl-10"
                      data-testid="input-company"
                    />
                  </div>
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="phone">Teléfono</Label>
                  <div className="relative">
                    <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <Input
                      id="phone"
                      name="phone"
                      value={personalData.phone}
                      onChange={handlePersonalChange}
                      disabled={!editingPersonal}
                      placeholder="+34 600 000 000"
                      className="pl-10"
                      data-testid="input-phone"
                    />
                  </div>
                </div>
              </div>
              
              {editingPersonal && (
                <div className="flex justify-end pt-4 border-t">
                  <Button onClick={savePersonalData} disabled={saving} className="btn-primary" data-testid="save-personal-btn">
                    {saving ? (
                      <div className="spinner w-4 h-4 border-2 border-white/30 border-t-white mr-2" />
                    ) : (
                      <Save className="w-4 h-4 mr-2" />
                    )}
                    Guardar cambios
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Billing Data Tab */}
        <TabsContent value="billing">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Datos de Facturación</CardTitle>
                <CardDescription>Información para las facturas</CardDescription>
              </div>
              {!editingBilling ? (
                <Button variant="outline" size="sm" onClick={() => setEditingBilling(true)} data-testid="edit-billing-btn">
                  <Edit2 className="w-4 h-4 mr-2" />
                  Editar
                </Button>
              ) : (
                <Button variant="ghost" size="sm" onClick={() => setEditingBilling(false)}>
                  <X className="w-4 h-4 mr-2" />
                  Cancelar
                </Button>
              )}
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="company_name">Nombre / Razón Social *</Label>
                  <div className="relative">
                    <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <Input
                      id="company_name"
                      name="company_name"
                      value={billingData.company_name}
                      onChange={handleBillingChange}
                      disabled={!editingBilling}
                      placeholder="Empresa S.L."
                      className="pl-10"
                      data-testid="input-company-name"
                    />
                  </div>
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="tax_id">NIF/CIF *</Label>
                  <div className="relative">
                    <FileText className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <Input
                      id="tax_id"
                      name="tax_id"
                      value={billingData.tax_id}
                      onChange={handleBillingChange}
                      disabled={!editingBilling}
                      placeholder="B12345678"
                      className="pl-10"
                      data-testid="input-tax-id"
                    />
                  </div>
                </div>
                
                <div className="space-y-2 md:col-span-2">
                  <Label htmlFor="address">Dirección *</Label>
                  <div className="relative">
                    <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <Input
                      id="address"
                      name="address"
                      value={billingData.address}
                      onChange={handleBillingChange}
                      disabled={!editingBilling}
                      placeholder="Calle Principal, 123"
                      className="pl-10"
                      data-testid="input-address"
                    />
                  </div>
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="city">Ciudad *</Label>
                  <Input
                    id="city"
                    name="city"
                    value={billingData.city}
                    onChange={handleBillingChange}
                    disabled={!editingBilling}
                    placeholder="Madrid"
                    data-testid="input-city"
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="postal_code">Código Postal *</Label>
                  <Input
                    id="postal_code"
                    name="postal_code"
                    value={billingData.postal_code}
                    onChange={handleBillingChange}
                    disabled={!editingBilling}
                    placeholder="28001"
                    data-testid="input-postal-code"
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="country">País</Label>
                  <div className="relative">
                    <Globe className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <Input
                      id="country"
                      name="country"
                      value={billingData.country}
                      onChange={handleBillingChange}
                      disabled={!editingBilling}
                      placeholder="España"
                      className="pl-10"
                      data-testid="input-country"
                    />
                  </div>
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="billing_email">Email de facturación</Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <Input
                      id="billing_email"
                      name="billing_email"
                      type="email"
                      value={billingData.billing_email}
                      onChange={handleBillingChange}
                      disabled={!editingBilling}
                      placeholder="facturacion@empresa.com"
                      className="pl-10"
                      data-testid="input-billing-email"
                    />
                  </div>
                  <p className="text-xs text-slate-500">Si está vacío, se usará el email de la cuenta</p>
                </div>
              </div>
              
              {editingBilling && (
                <div className="flex justify-end pt-4 border-t">
                  <Button onClick={saveBillingData} disabled={saving} className="btn-primary" data-testid="save-billing-btn">
                    {saving ? (
                      <div className="spinner w-4 h-4 border-2 border-white/30 border-t-white mr-2" />
                    ) : (
                      <Save className="w-4 h-4 mr-2" />
                    )}
                    Guardar datos de facturación
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Security Tab */}
        <TabsContent value="security">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Seguridad</CardTitle>
                <CardDescription>Gestiona tu contraseña</CardDescription>
              </div>
              {!editingPassword ? (
                <Button variant="outline" size="sm" onClick={() => setEditingPassword(true)} data-testid="edit-password-btn">
                  <Edit2 className="w-4 h-4 mr-2" />
                  Cambiar contraseña
                </Button>
              ) : (
                <Button variant="ghost" size="sm" onClick={() => {
                  setEditingPassword(false);
                  setPasswordData({ current_password: "", new_password: "", confirm_password: "" });
                }}>
                  <X className="w-4 h-4 mr-2" />
                  Cancelar
                </Button>
              )}
            </CardHeader>
            <CardContent>
              {!editingPassword ? (
                <div className="flex items-center gap-4 p-4 bg-slate-50 rounded-lg">
                  <div className="w-10 h-10 bg-slate-200 rounded-full flex items-center justify-center">
                    <Lock className="w-5 h-5 text-slate-500" />
                  </div>
                  <div>
                    <p className="font-medium text-slate-900">Contraseña</p>
                    <p className="text-sm text-slate-500">••••••••••••</p>
                  </div>
                </div>
              ) : (
                <div className="space-y-4 max-w-md">
                  <div className="space-y-2">
                    <Label htmlFor="current_password">Contraseña actual</Label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                      <Input
                        id="current_password"
                        name="current_password"
                        type="password"
                        value={passwordData.current_password}
                        onChange={handlePasswordChange}
                        placeholder="••••••••"
                        className="pl-10"
                        data-testid="input-current-password"
                      />
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="new_password">Nueva contraseña</Label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                      <Input
                        id="new_password"
                        name="new_password"
                        type="password"
                        value={passwordData.new_password}
                        onChange={handlePasswordChange}
                        placeholder="••••••••"
                        className="pl-10"
                        data-testid="input-new-password"
                      />
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="confirm_password">Confirmar nueva contraseña</Label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                      <Input
                        id="confirm_password"
                        name="confirm_password"
                        type="password"
                        value={passwordData.confirm_password}
                        onChange={handlePasswordChange}
                        placeholder="••••••••"
                        className="pl-10"
                        data-testid="input-confirm-password"
                      />
                    </div>
                  </div>
                  
                  <div className="flex justify-end pt-4">
                    <Button onClick={changePassword} disabled={saving} className="btn-primary" data-testid="save-password-btn">
                      {saving ? (
                        <div className="spinner w-4 h-4 border-2 border-white/30 border-t-white mr-2" />
                      ) : (
                        <Save className="w-4 h-4 mr-2" />
                      )}
                      Cambiar contraseña
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
          
          {/* Account Info Card */}
          <Card className="mt-6">
            <CardHeader>
              <CardTitle>Información de la cuenta</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-4 bg-slate-50 rounded-lg">
                  <p className="text-sm text-slate-500">Rol</p>
                  <p className="font-medium text-slate-900 capitalize">{user?.role || "Usuario"}</p>
                </div>
                <div className="p-4 bg-slate-50 rounded-lg">
                  <p className="text-sm text-slate-500">Máx. Proveedores</p>
                  <p className="font-medium text-slate-900">{user?.max_suppliers || 0}</p>
                </div>
                <div className="p-4 bg-slate-50 rounded-lg">
                  <p className="text-sm text-slate-500">Máx. Catálogos</p>
                  <p className="font-medium text-slate-900">{user?.max_catalogs || 0}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Soporte Tab */}
        <TabsContent value="support">
          <Support embedded={true} />
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default Profile;
