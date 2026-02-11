import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '@/components/landing/Header';
import Hero from '@/components/landing/Hero';
import Features from '@/components/landing/Features';
import HowItWorks from '@/components/landing/HowItWorks';
import Footer from '@/components/landing/Footer';
import { Language } from '@/components/landing/types';
import { useTranslation } from 'react-i18next';
// FEEDBACK FEATURE - remove this import to disable
import { FeedbackBanner } from '@/features/feedback';

export default function LandingPage() {
    const { i18n } = useTranslation();
    const navigate = useNavigate();
    // Normalize language: 'en-US' -> 'en', 'ru-RU' -> 'ru', fallback to 'en'
    const getBaseLanguage = (): Language => {
        const detected = i18n.language?.split('-')[0];
        return (detected === 'en' || detected === 'ru') ? detected : 'en';
    };
    const [lang, setLang] = useState<Language>(getBaseLanguage());

    const toggleLang = () => {
        const newLang = lang === 'en' ? 'ru' : 'en';
        setLang(newLang);
        i18n.changeLanguage(newLang);
    };

    return (
        <div className="min-h-screen bg-slate-900 text-white selection:bg-brand-500 selection:text-white">
            <Header lang={lang} toggleLang={toggleLang} />
            <main>
                <Hero lang={lang} />
                {/* FEEDBACK FEATURE - remove this block to disable */}
                <div className="max-w-5xl mx-auto px-6 py-4">
                    <FeedbackBanner onClick={() => navigate('/login')} />
                </div>
                <div id="features">
                    <Features lang={lang} />
                </div>
                <div id="how-it-works">
                    <HowItWorks lang={lang} />
                </div>
            </main>
            <Footer lang={lang} />
        </div>
    );
}
