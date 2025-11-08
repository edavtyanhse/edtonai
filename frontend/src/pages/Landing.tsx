import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { useNavigate } from "react-router-dom";
import { FileText, Target, Sparkles, ArrowRight, CheckCircle2, CircleCheck } from "lucide-react";
import heroImage from "@/assets/hero-illustration.svg";
import { HeroAnalysisPreview } from "@/components/landing/HeroAnalysisPreview";
import { ResumeInsightsCarousel } from "@/components/landing/ResumeInsightsCarousel";

const Landing = () => {
  const navigate = useNavigate();

  const features = [
    {
      icon: FileText,
      title: "1. Импортируйте резюме и вакансию",
      description: "Загрузите PDF/DOCX или вставьте ссылку на вакансию, EdTon автоматически выделит ключевые требования."
    },
    {
      icon: Target,
      title: "2. Получите аналитику совпадения",
      description:
        "AI сравнит опыт с вакансией, построит карту навыков и покажет, что усиливает отклик, а что стоит добавить."
    },
    {
      icon: Sparkles,
      title: "3. Экспортируйте адаптированные документы",
      description: "Скачайте обновлённое резюме, сопроводительное письмо и чек-лист действий в один клик."
    }
  ];

  const benefits = [
    {
      title: "Персонализация под каждую вакансию",
      description: "AI анализирует требования работодателя и адаптирует ваше резюме, подчёркивая релевантные навыки и опыт для конкретной позиции."
    },
    {
      title: "Анализ совпадения навыков",
      description: "Получите детальную информацию о том, насколько ваш профиль соответствует вакансии. Узнайте, какие навыки совпадают, а какие стоит добавить."
    },
    {
      title: "ATS-оптимизированные документы",
      description: "Резюме оптимизировано для прохождения автоматических систем отбора (ATS), используемых большинством крупных компаний."
    },
    {
      title: "Рекомендации от AI",
      description: "Получайте персональные рекомендации по улучшению резюме: какие навыки добавить, как лучше описать опыт, что подчеркнуть."
    },
    {
      title: "Готовые к отправке файлы",
      description: "Скачивайте адаптированное резюме в PDF или DOCX формате, а также персонализированное сопроводительное письмо."
    }
  ];

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg gradient-hero flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-primary-foreground" />
            </div>
            <span className="text-xl font-bold">EdTon.ai</span>
          </div>
          <nav className="hidden md:flex items-center gap-6">
            <a href="#features" className="text-muted-foreground hover:text-foreground transition-colors">
              Как работает
            </a>
            <a href="#benefits" className="text-muted-foreground hover:text-foreground transition-colors">
              Преимущества
            </a>
            <Button variant="outline" size="sm">Войти</Button>
          </nav>
        </div>
      </header>

      {/* Hero Section */}
      <section className="container mx-auto px-4 py-16 md:py-24">
        <div className="grid items-center gap-12 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.1fr)]">
          <div className="space-y-6 animate-fade-in">
            <div className="inline-flex items-center gap-2 rounded-full bg-primary/10 px-3 py-1 text-sm font-medium text-primary">
              <Sparkles className="h-4 w-4" />
              AI-конструктор откликов
            </div>
            <h1 className="text-3xl md:text-4xl lg:text-5xl font-bold leading-tight">
              Превратите резюме в точный ответ на вакансию за 5 минут
            </h1>
            <p className="text-base md:text-lg text-muted-foreground">
              EdTon.ai анализирует ваше резюме и требования работодателя, собирает сильные стороны и выдаёт готовые документы с рекомендациями по улучшению.
            </p>
            <div className="grid gap-4 text-sm text-muted-foreground sm:grid-cols-2">
              <div className="flex items-start gap-3">
                <CircleCheck className="mt-0.5 h-5 w-5 text-primary" />
                <p>Глубокий анализ hard и soft skills с оценкой совпадения.</p>
              </div>
              <div className="flex items-start gap-3">
                <CircleCheck className="mt-0.5 h-5 w-5 text-primary" />
                <p>Готовые версии резюме, письма и чек-лист действий.</p>
              </div>
              <div className="flex items-start gap-3">
                <CircleCheck className="mt-0.5 h-5 w-5 text-primary" />
                <p>AI-подсказки по тону, структуре и релевантным примерам.</p>
              </div>
              <div className="flex items-start gap-3">
                <CircleCheck className="mt-0.5 h-5 w-5 text-primary" />
                <p>Экспорт в PDF/DOCX и интеграция с ATS-требованиями.</p>
              </div>
            </div>
            <div className="flex flex-col gap-4 sm:flex-row">
              <Button
                size="lg"
                className="gradient-hero shadow-card hover:shadow-lg transition-all"
                onClick={() => navigate('/upload')}
              >
                Начать бесплатно
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
              <Button
                size="lg"
                variant="outline"
                onClick={() => {
                  const exampleSection = document.getElementById('example');
                  exampleSection?.scrollIntoView({ behavior: 'smooth' });
                }}
              >
                Посмотреть пример
              </Button>
            </div>
          </div>
          <div className="relative animate-slide-up space-y-6">
            <img
              src={heroImage}
              alt="EdTon.ai AI workflow illustration"
              className="w-full rounded-3xl border border-primary/10 shadow-card"
            />
            <HeroAnalysisPreview />
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="bg-secondary/30 py-16 md:py-24">
        <div className="container mx-auto px-4">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">Как это работает</h2>
            <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
              Три простых шага до идеального резюме
            </p>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <Card key={index} className="p-6 gradient-card border-0 shadow-soft hover:shadow-card transition-all">
                <div className="w-12 h-12 rounded-lg gradient-hero flex items-center justify-center mb-4">
                  <feature.icon className="w-6 h-6 text-primary-foreground" />
                </div>
                <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
                <p className="text-muted-foreground">{feature.description}</p>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Benefits Section */}
      <section id="benefits" className="py-16 md:py-24">
        <div className="container mx-auto px-4">
          <div className="max-w-3xl mx-auto">
            <div className="text-center mb-12">
              <h2 className="text-3xl md:text-4xl font-bold mb-4">Почему EdTon.ai</h2>
              <p className="text-muted-foreground text-lg">
                Все инструменты для успешного отклика в одном месте
              </p>
            </div>
            <Accordion type="single" collapsible className="space-y-4">
              {benefits.map((benefit, index) => (
                <AccordionItem 
                  key={index} 
                  value={`item-${index}`}
                  className="border rounded-lg bg-background shadow-soft hover:shadow-card transition-all px-6"
                >
                  <AccordionTrigger className="hover:no-underline">
                    <div className="flex items-center gap-3">
                      <CheckCircle2 className="w-5 h-5 text-success flex-shrink-0" />
                      <span className="text-lg font-medium text-left">{benefit.title}</span>
                    </div>
                  </AccordionTrigger>
                  <AccordionContent className="text-muted-foreground pl-8 pb-4">
                    {benefit.description}
                  </AccordionContent>
                </AccordionItem>
              ))}
            </Accordion>
            <div className="mt-8 text-center">
              <Button 
                size="lg" 
                className="gradient-hero shadow-card"
                onClick={() => navigate('/upload')}
              >
                Попробовать бесплатно
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Example Section */}
      <section id="example" className="bg-secondary/30 py-16 md:py-24">
        <div className="container mx-auto px-4">
          <div className="mx-auto max-w-5xl">
            <div className="text-center mb-12">
              <h2 className="text-3xl md:text-4xl font-bold mb-4">Пример работы</h2>
              <p className="text-muted-foreground text-lg">
                Посмотрите, как EdTon.ai расшифровывает сильные стороны и формирует выдачу
              </p>
            </div>
            <div className="grid gap-8 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)]">
              <Card className="p-8 shadow-card">
                <div className="space-y-6">
                  <div className="space-y-4">
                    <h3 className="flex items-center gap-2 text-xl font-semibold">
                      <FileText className="w-5 h-5 text-primary" />
                      Исходные данные
                    </h3>
                    <div className="grid gap-4 md:grid-cols-2">
                      <div className="rounded-xl border border-dashed border-primary/30 bg-secondary/40 p-4 text-sm">
                        <p className="font-medium mb-2">Резюме</p>
                        <p className="text-muted-foreground">Product Manager, 2 года · Финтех</p>
                        <p className="text-muted-foreground">SQL · Python · Discovery-интервью</p>
                      </div>
                      <div className="rounded-xl border border-dashed border-primary/30 bg-secondary/40 p-4 text-sm">
                        <p className="font-medium mb-2">Вакансия</p>
                        <p className="text-muted-foreground">Lead PM в EdTech, акцент на A/B тесты</p>
                        <p className="text-muted-foreground">Нужна экспертиза в образовательных продуктах</p>
                      </div>
                    </div>
                  </div>
                  <div className="flex justify-center">
                    <Sparkles className="h-10 w-10 text-primary animate-pulse-slow" />
                  </div>
                  <div className="space-y-4">
                    <h3 className="flex items-center gap-2 text-xl font-semibold">
                      <CheckCircle2 className="w-5 h-5 text-success" />
                      Что делает EdTon.ai
                    </h3>
                    <ul className="space-y-2 text-sm text-muted-foreground">
                      <li>• Сравнивает навыки и опыт с JD, подсвечивая совпадения и пробелы</li>
                      <li>• Переписывает блок опыта с акцентом на релевантные метрики</li>
                      <li>• Формирует рекомендации по следующему шагу и сопроводительное письмо</li>
                    </ul>
                  </div>
                </div>
              </Card>
              <div className="space-y-6">
                <HeroAnalysisPreview />
                <ResumeInsightsCarousel />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t py-8 bg-secondary/30">
        <div className="container mx-auto px-4">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded gradient-hero flex items-center justify-center">
                <Sparkles className="w-4 h-4 text-primary-foreground" />
              </div>
              <span className="font-semibold">EdTon.ai</span>
            </div>
            <div className="flex gap-6 text-sm text-muted-foreground">
              <a href="#" className="hover:text-foreground transition-colors">О проекте</a>
              <a href="#" className="hover:text-foreground transition-colors">Контакты</a>
              <a href="#" className="hover:text-foreground transition-colors">Конфиденциальность</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Landing;