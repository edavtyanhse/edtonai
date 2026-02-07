import React, { useState, useEffect } from 'react';
import { Menu, X, Globe, User as UserIcon, LogOut } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/context/AuthContext';
import { Language } from './types';

interface HeaderProps {
    lang: Language;
    toggleLang: () => void;
}

const Header: React.FC<HeaderProps> = ({ lang, toggleLang }) => {
    const [isScrolled, setIsScrolled] = useState(false);
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
    const { user, signOut } = useAuth();
    const navigate = useNavigate();

    useEffect(() => {
        const handleScroll = () => setIsScrolled(window.scrollY > 20);
        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    const content = {
        en: {
            features: 'Features',
            howItWorks: 'How it Works',
            login: 'Log In',
            getStarted: 'Get Started',
            history: 'History',
            logout: 'Log Out'
        },
        ru: {
            features: 'Возможности',
            howItWorks: 'Как это работает',
            login: 'Войти',
            getStarted: 'Начать',
            history: 'История версий',
            logout: 'Выйти'
        }
    };

    const t = content[lang];

    const handleLogout = async () => {
        await signOut();
        setMobileMenuOpen(false);
    };

    return (
        <header className={`fixed top-0 left-0 w-full z-50 transition-all duration-300 ${isScrolled ? 'bg-slate-900/80 backdrop-blur-lg border-b border-slate-800 py-3' : 'bg-transparent py-5'}`}>
            <div className="container mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between">
                <div className="flex items-center gap-2 font-bold text-2xl text-white">
                    <div className="w-8 h-8 bg-gradient-to-tr from-brand-600 to-indigo-500 rounded-lg flex items-center justify-center shadow-lg shadow-brand-500/20">
                        <span className="text-white">E</span>
                    </div>
                    EdtonAI
                </div>

                {/* Desktop Nav */}
                <nav className="hidden md:flex items-center gap-8">
                    <a href="#features" className="text-slate-300 hover:text-white text-sm font-medium transition-colors">{t.features}</a>
                    <a href="#how-it-works" className="text-slate-300 hover:text-white text-sm font-medium transition-colors">{t.howItWorks}</a>
                </nav>

                <div className="hidden md:flex items-center gap-4">
                    <button
                        onClick={toggleLang}
                        className="text-slate-300 hover:text-white flex items-center gap-1 text-sm font-medium uppercase"
                    >
                        <Globe className="w-4 h-4" />
                        {lang}
                    </button>
                    <div className="h-4 w-px bg-slate-700 mx-2"></div>

                    {user ? (
                        <>
                            <button onClick={handleLogout} className="text-slate-400 hover:text-white transition-colors flex items-center gap-2 text-sm font-medium">
                                <LogOut className="w-4 h-4" />
                                {t.logout}
                            </button>
                            <Link to="/history" className="bg-brand-600 hover:bg-brand-500 text-white px-5 py-2.5 rounded-lg text-sm font-bold transition-colors">
                                {t.history}
                            </Link>
                        </>
                    ) : (
                        <>
                            <Link to="/login" className="text-white font-medium text-sm hover:text-brand-300 transition-colors cursor-pointer">
                                {t.login}
                            </Link>
                            <Link to="/wizard" className="bg-white text-slate-900 px-5 py-2.5 rounded-lg text-sm font-bold hover:bg-slate-200 transition-colors">
                                {t.getStarted}
                            </Link>
                        </>
                    )}
                </div>

                {/* Mobile Menu Button */}
                <button
                    className="md:hidden text-white"
                    onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                >
                    {mobileMenuOpen ? <X /> : <Menu />}
                </button>
            </div>

            {/* Mobile Menu */}
            {mobileMenuOpen && (
                <div className="md:hidden absolute top-full left-0 w-full bg-slate-900 border-b border-slate-800 p-4 flex flex-col gap-4 animate-in slide-in-from-top-2">
                    <a href="#features" onClick={() => setMobileMenuOpen(false)} className="text-slate-300 hover:text-white py-2">{t.features}</a>
                    <a href="#how-it-works" onClick={() => setMobileMenuOpen(false)} className="text-slate-300 hover:text-white py-2">{t.howItWorks}</a>
                    <div className="h-px bg-slate-800 my-2" />
                    <button
                        onClick={() => { toggleLang(); setMobileMenuOpen(false); }}
                        className="text-slate-300 hover:text-white py-2 flex items-center gap-2 uppercase"
                    >
                        <Globe className="w-4 h-4" /> Switch to {lang === 'en' ? 'RU' : 'EN'}
                    </button>

                    {user ? (
                        <>
                            <div className="flex flex-col gap-2 mt-4">
                                <Link to="/history" onClick={() => setMobileMenuOpen(false)} className="bg-brand-600 text-white text-center py-3 rounded-lg font-bold flex items-center justify-center gap-2">
                                    <UserIcon className="w-4 h-4" /> {t.history}
                                </Link>
                                <button onClick={handleLogout} className="text-slate-400 py-2 text-left flex items-center gap-2 justify-center">
                                    <LogOut className="w-4 h-4" /> {t.logout}
                                </button>
                            </div>
                        </>
                    ) : (
                        <>
                            <Link to="/login" onClick={() => setMobileMenuOpen(false)} className="text-white font-medium py-2 text-left">
                                {t.login}
                            </Link>
                            <Link to="/wizard" onClick={() => setMobileMenuOpen(false)} className="bg-brand-600 text-white text-center py-3 rounded-lg font-bold">
                                {t.getStarted}
                            </Link>
                        </>
                    )}
                </div>
            )}
        </header>
    );
};

export default Header;
