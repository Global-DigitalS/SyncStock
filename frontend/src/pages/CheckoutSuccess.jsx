import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../App";
import { toast } from "sonner";
import axios from "axios";
import { Package, CheckCircle2, AlertCircle } from "lucide-react";
import { Button } from "../components/ui/button";
import { sanitizeEmail, sanitizeString } from "../utils/sanitizer";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const CheckoutSuccess = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [status, setStatus] = useState("loading"); // loading, success, error
  const [message, setMessage] = useState("Verificando pago...");
  const [errorDetails, setErrorDetails] = useState("");

  useEffect(() => {
    const verifyAndRegister = async () => {
      try {
        const sessionId = searchParams.get("session_id");
        if (!sessionId) {
          setStatus("error");
          setMessage("No se encontró la sesión de pago");
          return;
        }

        // Check if payment was successful
        const statusRes = await axios.get(
          `${BACKEND_URL}/api/stripe/checkout-status/${sessionId}`,
          { withCredentials: true }
        );

        const paymentStatus = statusRes.data?.payment_status;

        // If payment not confirmed yet, retry in a few seconds
        if (paymentStatus !== "paid") {
          setStatus("error");
          setMessage("El pago no ha sido confirmado");
          setErrorDetails("Por favor intenta de nuevo o contacta al soporte");
          return;
        }

        // Payment confirmed! Now register the user
        const pendingReg = sessionStorage.getItem("pending_registration");
        const pendingBilling = sessionStorage.getItem("pending_billing");

        if (!pendingReg) {
          setStatus("error");
          setMessage("No se encontraron los datos de registro");
          setErrorDetails("Sesión expirada. Por favor intenta registrarte de nuevo");
          return;
        }

        const regData = JSON.parse(pendingReg);
        const billingData = JSON.parse(pendingBilling || "{}");

        // Step 1: Register the user
        const registerRes = await axios.post(`${BACKEND_URL}/api/auth/register`, {
          name: sanitizeString(regData.name),
          email: sanitizeEmail(regData.email),
          password: regData.password,
          company: null,
          plan_id: regData.plan_id
        });

        const token = registerRes.data.token;

        // Get CSRF token
        let csrfToken = null;
        try {
          const match = document.cookie.match(new RegExp("(^| )csrf_token=([^;]+)"));
          csrfToken = match ? match[2] : null;
        } catch (e) {
          // Ignore
        }

        // Step 2: Save billing information
        const billingConfig = {
          headers: { Authorization: `Bearer ${token}` }
        };
        if (csrfToken) {
          billingConfig.headers["X-CSRF-Token"] = csrfToken;
        }

        await axios.post(
          `${BACKEND_URL}/api/subscriptions/billing-info`,
          {
            ...billingData,
            billing_email: regData.email
          },
          billingConfig
        );

        // Clear temporary data
        sessionStorage.removeItem("pending_registration");
        sessionStorage.removeItem("pending_billing");
        sessionStorage.removeItem("stripe_session_id");

        setStatus("success");
        setMessage("¡Cuenta creada exitosamente!");

        // Redirect to dashboard after 2 seconds
        setTimeout(() => {
          navigate("/");
        }, 2000);
      } catch (error) {
        console.error("Checkout error:", error);
        setStatus("error");

        if (error.response?.status === 401) {
          // User doesn't exist yet - try without auth
          setMessage("Verificando pago...");
          // Could add auto-retry here
        } else {
          setMessage("Error al procesar el registro");
          setErrorDetails(error.response?.data?.detail || error.message);
        }
      }
    };

    // Small delay to ensure backend has processed webhook
    const timer = setTimeout(verifyAndRegister, 1000);
    return () => clearTimeout(timer);
  }, [searchParams, navigate]);

  if (status === "loading") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100">
        <div className="text-center">
          <div className="spinner w-12 h-12 border-4 border-indigo-200 border-t-indigo-600 mx-auto mb-4" />
          <p className="text-slate-600">Verificando pago...</p>
        </div>
      </div>
    );
  }

  if (status === "success") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 p-4">
        <div className="bg-white rounded-lg shadow-lg p-8 max-w-md w-full text-center">
          <div className="mb-4 flex justify-center">
            <CheckCircle2 className="w-16 h-16 text-green-500" strokeWidth={1.5} />
          </div>
          <h1 className="text-2xl font-bold text-slate-900 mb-2">{message}</h1>
          <p className="text-slate-600 mb-6">
            Tu cuenta está lista. Redirigiendo al panel...
          </p>
          <Button
            onClick={() => navigate("/")}
            className="w-full bg-indigo-600 hover:bg-indigo-700 text-white"
          >
            Ir al Panel
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 p-4">
      <div className="bg-white rounded-lg shadow-lg p-8 max-w-md w-full">
        <div className="mb-4 flex justify-center">
          <AlertCircle className="w-16 h-16 text-red-500" strokeWidth={1.5} />
        </div>
        <h1 className="text-2xl font-bold text-slate-900 mb-2">{message}</h1>
        {errorDetails && (
          <p className="text-slate-600 mb-6 text-sm">{errorDetails}</p>
        )}
        <div className="space-y-3">
          <Button
            onClick={() => navigate("/register")}
            className="w-full bg-indigo-600 hover:bg-indigo-700 text-white"
          >
            Intentar de Nuevo
          </Button>
          <Button
            onClick={() => navigate("/login")}
            variant="outline"
            className="w-full"
          >
            Ir a Login
          </Button>
        </div>
      </div>
    </div>
  );
};

export default CheckoutSuccess;
