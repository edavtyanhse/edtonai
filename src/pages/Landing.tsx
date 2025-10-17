import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useNavigate } from "react-router-dom";
import { FileText, Target, Sparkles, ArrowRight, CheckCircle2 } from "lucide-react";
import heroImage from "@/assets/hero-image.jpg";

const Landing = () => {
  const navigate = useNavigate();

  const features = [
    {
      icon: FileText,
      title: "Загрузите резюме",
      description: "Быстрая загрузка вашего резюме в PDF или DOCX формате"
    },
    {
      icon: Target,
      title: "Система анализирует",
      description: "AI проверяет совпадения с требованиями вакансии"
    },
    {
      icon: Sparkles,
      title: "Получите результат",
      description: "Адаптированное резюме и сопроводительное письмо за минуты"
    }
  ];

  const benefits = [
    "Персонализация под каждую вакансию",
    "Анализ совпадения навыков",
    "ATS-оптимизированные документы",
    "Рекомендации от AI",
    "Готовые к отправке файлы"
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
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          <div className="space-y-6 animate-fade-in">
            <div className="inline-block px-3 py-1 rounded-full bg-primary/10 text-primary text-sm font-medium">
              Powered by AI
            </div>
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold leading-tight">
              Создай персонализированное резюме за минуты
            </h1>
            <p className="text-lg text-muted-foreground">
              Вставь вакансию — получи адаптированное резюме и письмо с рекомендациями от AI
            </p>
            <div className="flex flex-col sm:flex-row gap-4">
              <Button 
                size="lg" 
                className="gradient-hero text-lg shadow-card hover:shadow-lg transition-all"
                onClick={() => navigate('/upload')}
              >
                Начать бесплатно
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
              <Button size="lg" variant="outline" className="text-lg">
                Посмотреть пример
              </Button>
            </div>
          </div>
          <div className="relative animate-slide-up">
            <img 
              src={heroImage} 
              alt="EdTon.ai Interface" 
              className="rounded-2xl shadow-card w-full"
            />
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
            <div className="grid gap-4">
              {benefits.map((benefit, index) => (
                <div 
                  key={index} 
                  className="flex items-center gap-3 p-4 rounded-lg bg-background border shadow-soft hover:shadow-card transition-all"
                >
                  <CheckCircle2 className="w-6 h-6 text-success flex-shrink-0" />
                  <span className="text-lg">{benefit}</span>
                </div>
              ))}
            </div>
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