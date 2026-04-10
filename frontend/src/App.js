import "@/index.css";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import { WebSocketProvider } from "./contexts/WebSocketContext";
import { LanguageProvider } from "./contexts/LanguageContext";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { Layout } from "./components/Layout";
import { Login } from "./pages/Login";
import { Register } from "./pages/Register";
import { Dashboard } from "./pages/Dashboard";
import { Clients } from "./pages/Clients";
import { Appartements } from "./pages/Appartements";
import { WhatsApp } from "./pages/WhatsApp";
import { Parametres } from "./pages/Parametres";
import { Prospects } from "./pages/Prospects";
import { AuditLog } from "./pages/AuditLog";
import { Corbeille } from "./pages/Corbeille";
import { Admin } from "./pages/Admin";
import { ClientsEnDouble } from "./pages/ClientsEnDouble";
import { Toaster } from "./components/ui/sonner";

function App() {
  return (
    <LanguageProvider>
      <AuthProvider>
        <WebSocketProvider>
          <Toaster position="top-right" richColors />
          <BrowserRouter>
            <Routes>
              {/* Public routes */}
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />

              {/* Protected routes */}
              <Route
                path="/"
                element={
                  <ProtectedRoute>
                    <Layout>
                      <Dashboard />
                    </Layout>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/clients"
                element={
                  <ProtectedRoute>
                    <Layout>
                      <Clients />
                    </Layout>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/appartements"
                element={
                  <ProtectedRoute>
                    <Layout>
                      <Appartements />
                    </Layout>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/whatsapp"
                element={
                  <ProtectedRoute>
                    <Layout>
                      <WhatsApp />
                    </Layout>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/prospects"
                element={
                  <ProtectedRoute>
                    <Layout>
                      <Prospects />
                    </Layout>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/audit-log"
                element={
                  <ProtectedRoute>
                    <Layout>
                      <AuditLog />
                    </Layout>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/corbeille"
                element={
                  <ProtectedRoute>
                    <Layout>
                      <Corbeille />
                    </Layout>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/parametres"
                element={
                  <ProtectedRoute>
                    <Layout>
                      <Parametres />
                    </Layout>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/admin"
                element={
                  <ProtectedRoute>
                    <Layout>
                      <Admin />
                    </Layout>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/doublons"
                element={
                  <ProtectedRoute>
                    <Layout>
                      <ClientsEnDouble />
                    </Layout>
                  </ProtectedRoute>
                }
              />

              {/* Redirect unknown routes */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </BrowserRouter>
        </WebSocketProvider>
      </AuthProvider>
    </LanguageProvider>
  );
}

export default App;
