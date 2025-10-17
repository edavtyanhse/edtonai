import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import { Sparkles, CheckCircle2, FileText, Mail, Download, Eye, Copy } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

const Results = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [isGenerating, setIsGenerating] = useState(true);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    // Simulate generation progress
    const interval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval);
          setIsGenerating(false);
          return 100;
        }
        return prev + 10;
      });
    }, 300);

    return () => clearInterval(interval);
  }, []);

  const handleDownload = (type: string) => {
    toast({
      title: "Скачивание началось",
      description: `${type} будет сохранён на вашем устройстве`,
    });
  };

  const handleCopy = () => {
    toast({
      title: "Скопировано",
      description: "Текст письма скопирован в буфер обмена",
    });
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2 cursor-pointer" onClick={() => navigate('/')}>
            <div className="w-8 h-8 rounded-lg gradient-hero flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-primary-foreground" />
            </div>
            <span className="text-xl font-bold">EdTon.ai</span>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-12">
        {/* Progress Steps */}
        <div className="max-w-4xl mx-auto mb-12">
          <div className="flex items-center justify-between">
            <div className="flex flex-col items-center gap-2">
              <div className="w-10 h-10 rounded-full bg-success flex items-center justify-center text-success-foreground">
                <CheckCircle2 className="w-5 h-5" />
              </div>
              <span className="text-sm font-medium">Загрузка</span>
            </div>
            <div className="flex-1 h-0.5 bg-primary mx-4" />
            <div className="flex flex-col items-center gap-2">
              <div className="w-10 h-10 rounded-full bg-success flex items-center justify-center text-success-foreground">
                <CheckCircle2 className="w-5 h-5" />
              </div>
              <span className="text-sm font-medium">Анализ</span>
            </div>
            <div className="flex-1 h-0.5 bg-primary mx-4" />
            <div className="flex flex-col items-center gap-2">
              <div className="w-10 h-10 rounded-full gradient-hero flex items-center justify-center text-primary-foreground font-semibold">
                3
              </div>
              <span className="text-sm font-medium">Генерация</span>
            </div>
          </div>
        </div>

        <div className="max-w-5xl mx-auto space-y-8">
          {isGenerating ? (
            // Generation Progress
            <Card className="p-12 shadow-card text-center animate-fade-in">
              <div className="space-y-6">
                <div className="w-16 h-16 rounded-full gradient-hero flex items-center justify-center mx-auto">
                  <Sparkles className="w-8 h-8 text-primary-foreground animate-pulse-slow" />
                </div>
                <h2 className="text-2xl font-semibold">AI адаптирует ваши документы...</h2>
                <p className="text-muted-foreground">
                  Создаём персонализированное резюме и сопроводительное письмо
                </p>
                <div className="space-y-2">
                  <div className="h-2 bg-secondary rounded-full overflow-hidden">
                    <div 
                      className="h-full gradient-hero transition-all duration-300"
                      style={{ width: `${progress}%` }}
                    />
                  </div>
                  <p className="text-sm text-muted-foreground">{progress}%</p>
                </div>
              </div>
            </Card>
          ) : (
            // Generated Documents
            <>
              <div className="text-center space-y-2 animate-fade-in">
                <div className="flex items-center justify-center gap-2 mb-4">
                  <CheckCircle2 className="w-8 h-8 text-success" />
                </div>
                <h1 className="text-3xl md:text-4xl font-bold">Документы готовы!</h1>
                <p className="text-muted-foreground text-lg">
                  Ваши документы адаптированы под вакансию и готовы к отправке
                </p>
              </div>

              <div className="grid md:grid-cols-2 gap-6">
                {/* Resume Card */}
                <Card className="p-6 shadow-soft hover:shadow-card transition-all animate-slide-up">
                  <div className="space-y-4">
                    <div className="flex items-start gap-4">
                      <div className="w-12 h-12 rounded-lg gradient-hero flex items-center justify-center flex-shrink-0">
                        <FileText className="w-6 h-6 text-primary-foreground" />
                      </div>
                      <div className="flex-1">
                        <h3 className="text-xl font-semibold mb-1">Адаптированное резюме</h3>
                        <p className="text-sm text-muted-foreground">
                          Оптимизировано под требования вакансии "Product Manager в EdTech"
                        </p>
                      </div>
                    </div>
                    
                    <div className="p-4 rounded-lg bg-secondary/50 space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Совпадение с вакансией</span>
                        <span className="font-semibold text-primary">76%</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">ATS-оптимизация</span>
                        <span className="font-semibold text-success">94%</span>
                      </div>
                    </div>

                    <div className="flex flex-col gap-2">
                      <Button variant="outline" className="w-full">
                        <Eye className="w-4 h-4 mr-2" />
                        Просмотреть
                      </Button>
                      <div className="grid grid-cols-2 gap-2">
                        <Button variant="outline" size="sm" onClick={() => handleDownload("PDF")}>
                          <Download className="w-4 h-4 mr-1" />
                          PDF
                        </Button>
                        <Button variant="outline" size="sm" onClick={() => handleDownload("DOCX")}>
                          <Download className="w-4 h-4 mr-1" />
                          DOCX
                        </Button>
                      </div>
                    </div>
                  </div>
                </Card>

                {/* Cover Letter Card */}
                <Card className="p-6 shadow-soft hover:shadow-card transition-all animate-slide-up">
                  <div className="space-y-4">
                    <div className="flex items-start gap-4">
                      <div className="w-12 h-12 rounded-lg bg-accent flex items-center justify-center flex-shrink-0">
                        <Mail className="w-6 h-6 text-accent-foreground" />
                      </div>
                      <div className="flex-1">
                        <h3 className="text-xl font-semibold mb-1">Сопроводительное письмо</h3>
                        <p className="text-sm text-muted-foreground">
                          Персонализированное письмо для максимального вовлечения
                        </p>
                      </div>
                    </div>
                    
                    <div className="p-4 rounded-lg bg-secondary/50 space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Ключевые навыки</span>
                        <span className="font-semibold">5 упомянуто</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Релевантность</span>
                        <span className="font-semibold text-success">Высокая</span>
                      </div>
                    </div>

                    <div className="flex flex-col gap-2">
                      <Button variant="outline" className="w-full">
                        <Eye className="w-4 h-4 mr-2" />
                        Просмотреть
                      </Button>
                      <div className="grid grid-cols-2 gap-2">
                        <Button variant="outline" size="sm" onClick={handleCopy}>
                          <Copy className="w-4 h-4 mr-1" />
                          Копировать
                        </Button>
                        <Button variant="outline" size="sm" onClick={() => handleDownload("Письмо")}>
                          <Download className="w-4 h-4 mr-1" />
                          Скачать
                        </Button>
                      </div>
                    </div>
                  </div>
                </Card>
              </div>

              {/* AI Summary */}
              <Card className="p-6 shadow-soft bg-primary/5 border-primary/20 animate-slide-up">
                <div className="flex gap-4">
                  <Sparkles className="w-6 h-6 text-primary flex-shrink-0" />
                  <div className="space-y-2">
                    <h3 className="font-semibold text-lg">Результаты анализа AI</h3>
                    <p className="text-sm text-muted-foreground">
                      Ваше резюме адаптировано под вакансию <span className="font-medium text-foreground">"Product Manager в EdTech"</span>.
                      Совпадение составляет <span className="font-semibold text-primary">76%</span>. Рекомендуется добавить примеры опыта 
                      работы с A/B тестированием для повышения релевантности.
                    </p>
                  </div>
                </div>
              </Card>

              {/* Actions */}
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Button
                  size="lg"
                  variant="outline"
                  onClick={() => navigate('/upload')}
                >
                  Создать новый отклик
                </Button>
                <Button
                  size="lg"
                  className="gradient-hero shadow-card"
                  onClick={() => navigate('/')}
                >
                  Вернуться на главную
                </Button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default Results;