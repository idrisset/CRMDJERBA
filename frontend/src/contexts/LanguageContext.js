import { createContext, useContext, useState, useEffect } from 'react';

const LanguageContext = createContext(null);

const translations = {
  fr: {
    // Navigation
    dashboard: 'Tableau de bord',
    clients: 'Clients',
    apartments: 'Appartements',
    whatsapp: 'IA WhatsApp',
    settings: 'Paramètres',
    logout: 'Déconnexion',
    
    // Auth
    login: 'Connexion',
    register: "S'inscrire",
    email: 'Email',
    password: 'Mot de passe',
    name: 'Nom complet',
    signIn: 'Se connecter',
    signUp: 'Créer un compte',
    noAccount: 'Pas encore de compte?',
    hasAccount: 'Déjà un compte?',
    createAccount: 'Créer un compte',
    
    // Dashboard
    totalClients: 'Total Clients',
    availableApts: 'Disponibles',
    reservedApts: 'Réservés',
    soldApts: 'Vendus',
    hotLeads: 'Leads Chauds',
    whatsappLeads: 'Leads WhatsApp',
    recentClients: 'Clients Récents',
    clientsByStatus: 'Clients par Statut',
    overview: "Vue d'ensemble de votre activité",
    
    // Clients
    addClient: 'Ajouter un client',
    editClient: 'Modifier le client',
    phone: 'Téléphone',
    salary: 'Salaire',
    situation: 'Situation familiale',
    notes: 'Notes',
    status: 'Statut',
    temperature: 'Température',
    apartment: 'Appartement',
    actions: 'Actions',
    search: 'Rechercher...',
    filterByStatus: 'Filtrer par statut',
    allStatuses: 'Tous les statuts',
    noClients: 'Aucun client trouvé',
    
    // Statuses
    new: 'Nouveau',
    interested: 'Intéressé',
    visit: 'Visite',
    reserved: 'Réservé',
    sold: 'Vendu',
    hot: 'Chaud',
    warm: 'Tiède',
    cold: 'Froid',
    
    // Apartments
    addApartment: 'Ajouter un appartement',
    editApartment: "Modifier l'appartement",
    residence: 'Résidence',
    type: 'Type',
    price: 'Prix',
    floor: 'Étage',
    surface: 'Surface',
    available: 'Disponible',
    noApartments: 'Aucun appartement',
    
    // Settings
    residences: 'Résidences',
    users: 'Utilisateurs',
    notifications: 'Notifications',
    addResidence: 'Ajouter une résidence',
    editResidence: 'Modifier la résidence',
    address: 'Adresse',
    description: 'Description',
    admin: 'Administrateur',
    commercial: 'Commercial',
    emailNotifications: 'Notifications par email',
    notificationEmails: 'Emails de notification',
    
    // WhatsApp
    testAI: "Tester l'agent IA",
    aiConfig: 'Configuration IA',
    aiActive: 'Agent actif',
    conversationHistory: 'Historique des conversations',
    sendMessage: 'Envoyer',
    typeMessage: 'Tapez un message...',
    noConversations: 'Aucune conversation',
    
    // Export
    exportExcel: 'Exporter Excel',
    exportPDF: 'Exporter PDF',
    
    // Common
    save: 'Enregistrer',
    cancel: 'Annuler',
    delete: 'Supprimer',
    edit: 'Modifier',
    create: 'Créer',
    loading: 'Chargement...',
    online: 'En ligne',
    offline: 'Hors ligne',
    success: 'Succès',
    error: 'Erreur',
    confirm: 'Confirmer',
    none: 'Aucun',
  },
  ar: {
    // Navigation
    dashboard: 'لوحة التحكم',
    clients: 'العملاء',
    apartments: 'الشقق',
    whatsapp: 'واتساب الذكي',
    settings: 'الإعدادات',
    logout: 'تسجيل الخروج',
    
    // Auth
    login: 'تسجيل الدخول',
    register: 'التسجيل',
    email: 'البريد الإلكتروني',
    password: 'كلمة المرور',
    name: 'الاسم الكامل',
    signIn: 'دخول',
    signUp: 'إنشاء حساب',
    noAccount: 'ليس لديك حساب؟',
    hasAccount: 'لديك حساب؟',
    createAccount: 'إنشاء حساب',
    
    // Dashboard
    totalClients: 'إجمالي العملاء',
    availableApts: 'متوفرة',
    reservedApts: 'محجوزة',
    soldApts: 'مباعة',
    hotLeads: 'عملاء ساخنون',
    whatsappLeads: 'عملاء واتساب',
    recentClients: 'العملاء الأخيرون',
    clientsByStatus: 'العملاء حسب الحالة',
    overview: 'نظرة عامة على نشاطك',
    
    // Clients
    addClient: 'إضافة عميل',
    editClient: 'تعديل العميل',
    phone: 'الهاتف',
    salary: 'الراتب',
    situation: 'الحالة العائلية',
    notes: 'ملاحظات',
    status: 'الحالة',
    temperature: 'درجة الاهتمام',
    apartment: 'الشقة',
    actions: 'إجراءات',
    search: 'بحث...',
    filterByStatus: 'تصفية حسب الحالة',
    allStatuses: 'جميع الحالات',
    noClients: 'لا يوجد عملاء',
    
    // Statuses
    new: 'جديد',
    interested: 'مهتم',
    visit: 'زيارة',
    reserved: 'محجوز',
    sold: 'مباع',
    hot: 'ساخن',
    warm: 'دافئ',
    cold: 'بارد',
    
    // Apartments
    addApartment: 'إضافة شقة',
    editApartment: 'تعديل الشقة',
    residence: 'المجمع السكني',
    type: 'النوع',
    price: 'السعر',
    floor: 'الطابق',
    surface: 'المساحة',
    available: 'متوفر',
    noApartments: 'لا توجد شقق',
    
    // Settings
    residences: 'المجمعات السكنية',
    users: 'المستخدمون',
    notifications: 'الإشعارات',
    addResidence: 'إضافة مجمع',
    editResidence: 'تعديل المجمع',
    address: 'العنوان',
    description: 'الوصف',
    admin: 'مدير',
    commercial: 'تجاري',
    emailNotifications: 'إشعارات البريد',
    notificationEmails: 'بريد الإشعارات',
    
    // WhatsApp
    testAI: 'اختبار الذكاء الاصطناعي',
    aiConfig: 'إعدادات الذكاء',
    aiActive: 'الوكيل نشط',
    conversationHistory: 'سجل المحادثات',
    sendMessage: 'إرسال',
    typeMessage: 'اكتب رسالة...',
    noConversations: 'لا توجد محادثات',
    
    // Export
    exportExcel: 'تصدير Excel',
    exportPDF: 'تصدير PDF',
    
    // Common
    save: 'حفظ',
    cancel: 'إلغاء',
    delete: 'حذف',
    edit: 'تعديل',
    create: 'إنشاء',
    loading: 'جاري التحميل...',
    online: 'متصل',
    offline: 'غير متصل',
    success: 'نجاح',
    error: 'خطأ',
    confirm: 'تأكيد',
    none: 'لا شيء',
  },
  en: {
    // Navigation
    dashboard: 'Dashboard',
    clients: 'Clients',
    apartments: 'Apartments',
    whatsapp: 'WhatsApp AI',
    settings: 'Settings',
    logout: 'Logout',
    
    // Auth
    login: 'Login',
    register: 'Register',
    email: 'Email',
    password: 'Password',
    name: 'Full Name',
    signIn: 'Sign In',
    signUp: 'Sign Up',
    noAccount: "Don't have an account?",
    hasAccount: 'Already have an account?',
    createAccount: 'Create Account',
    
    // Dashboard
    totalClients: 'Total Clients',
    availableApts: 'Available',
    reservedApts: 'Reserved',
    soldApts: 'Sold',
    hotLeads: 'Hot Leads',
    whatsappLeads: 'WhatsApp Leads',
    recentClients: 'Recent Clients',
    clientsByStatus: 'Clients by Status',
    overview: 'Overview of your activity',
    
    // Clients
    addClient: 'Add Client',
    editClient: 'Edit Client',
    phone: 'Phone',
    salary: 'Salary',
    situation: 'Family Status',
    notes: 'Notes',
    status: 'Status',
    temperature: 'Temperature',
    apartment: 'Apartment',
    actions: 'Actions',
    search: 'Search...',
    filterByStatus: 'Filter by status',
    allStatuses: 'All statuses',
    noClients: 'No clients found',
    
    // Statuses
    new: 'New',
    interested: 'Interested',
    visit: 'Visit',
    reserved: 'Reserved',
    sold: 'Sold',
    hot: 'Hot',
    warm: 'Warm',
    cold: 'Cold',
    
    // Apartments
    addApartment: 'Add Apartment',
    editApartment: 'Edit Apartment',
    residence: 'Residence',
    type: 'Type',
    price: 'Price',
    floor: 'Floor',
    surface: 'Surface',
    available: 'Available',
    noApartments: 'No apartments',
    
    // Settings
    residences: 'Residences',
    users: 'Users',
    notifications: 'Notifications',
    addResidence: 'Add Residence',
    editResidence: 'Edit Residence',
    address: 'Address',
    description: 'Description',
    admin: 'Administrator',
    commercial: 'Commercial',
    emailNotifications: 'Email Notifications',
    notificationEmails: 'Notification Emails',
    
    // WhatsApp
    testAI: 'Test AI Agent',
    aiConfig: 'AI Configuration',
    aiActive: 'Agent Active',
    conversationHistory: 'Conversation History',
    sendMessage: 'Send',
    typeMessage: 'Type a message...',
    noConversations: 'No conversations',
    
    // Export
    exportExcel: 'Export Excel',
    exportPDF: 'Export PDF',
    
    // Common
    save: 'Save',
    cancel: 'Cancel',
    delete: 'Delete',
    edit: 'Edit',
    create: 'Create',
    loading: 'Loading...',
    online: 'Online',
    offline: 'Offline',
    success: 'Success',
    error: 'Error',
    confirm: 'Confirm',
    none: 'None',
  }
};

export function LanguageProvider({ children }) {
  const [language, setLanguage] = useState(() => {
    return localStorage.getItem('language') || 'fr';
  });

  useEffect(() => {
    localStorage.setItem('language', language);
    document.documentElement.dir = language === 'ar' ? 'rtl' : 'ltr';
    document.documentElement.lang = language;
  }, [language]);

  const t = (key) => {
    return translations[language]?.[key] || translations['fr']?.[key] || key;
  };

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within LanguageProvider');
  }
  return context;
}
