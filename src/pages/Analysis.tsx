import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { useNavigate } from "react-router-dom";
import { Sparkles, CheckCircle2, AlertCircle, Lightbulb, ArrowRight } from "lucide-react";

const Analysis = () => {
  const navigate = useNavigate();
  const matchPercentage = 76;

  const matchingSkills = [
    { name: "Product Management", level: "high" },
    { name: "SQL", level: "high" },
    { name: "Python", level: "medium" },
    { name: "Roadmap Planning", level: "high" },
    { name: "Data Analysis", level: "medium" },
  ];

  const missingSkills = [
    { name: "A/B Testing", importance: "high" },
    { name: "EdTech Experience", importance: "medium" },
    { name: "Learning Analytics", importance: "medium" },
  ];

  const recommendations = [
    "Добавьте конкретные примеры A/B тестов из предыдущего опыта",
    "Подчеркните опыт работы с образовательными проектами или продуктами",
    "Укажите знакомство с метриками обучения и engagement студентов",
    "Добавьте примеры успешного запуска образовательных фич",
  ];

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
              <div className="w-10 h-10 rounded-full gradient-hero flex items-center justify-center text-primary-foreground font-semibold">
                2
              </div>
              <span className="text-sm font-medium">Анализ</span>
            </div>
            <div className="flex-1 h-0.5 bg-border mx-4" />
            <div className="flex flex-col items-center gap-2">
              <div className="w-10 h-10 rounded-full bg-secondary flex items-center justify-center text-muted-foreground font-semibold">
                3
              </div>
              <span className="text-sm text-muted-foreground">Генерация</span>
            </div>
          </div>
        </div>

        {/* Analysis Results */}
        <div className="max-w-5xl mx-auto space-y-8">
          <div className="text-center space-y-2 animate-fade-in">
            <h1 className="text-3xl md:text-4xl font-bold">Результат анализа</h1>
            <p className="text-muted-foreground text-lg">
              Ваше резюме проанализировано для вакансии "Product Manager в EdTech"
            </p>
          </div>

          {/* Match Score */}
          <Card className="p-8 shadow-card animate-slide-up">
            <div className="flex flex-col md:flex-row items-center gap-8">
              <div className="relative w-40 h-40">
                <svg className="w-full h-full transform -rotate-90">
                  <circle
                    cx="80"
                    cy="80"
                    r="70"
                    fill="none"
                    stroke="hsl(var(--secondary))"
                    strokeWidth="12"
                  />
                  <circle
                    cx="80"
                    cy="80"
                    r="70"
                    fill="none"
                    stroke="hsl(var(--primary))"
                    strokeWidth="12"
                    strokeDasharray={`${2 * Math.PI * 70}`}
                    strokeDashoffset={`${2 * Math.PI * 70 * (1 - matchPercentage / 100)}`}
                    className="transition-all duration-1000"
                  />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className="text-4xl font-bold text-primary">{matchPercentage}%</span>
                  <span className="text-sm text-muted-foreground">совпадение</span>
                </div>
              </div>
              <div className="flex-1 space-y-4">
                <h2 className="text-2xl font-semibold">Хорошее соответствие!</h2>
                <p className="text-muted-foreground">
                  Ваш профиль хорошо подходит для данной позиции. С небольшими улучшениями вы значительно 
                  повысите шансы на получение приглашения.
                </p>
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span>Ключевые навыки</span>
                    <span className="font-medium">85%</span>
                  </div>
                  <Progress value={85} className="h-2" />
                </div>
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span>Опыт и требования</span>
                    <span className="font-medium">72%</span>
                  </div>
                  <Progress value={72} className="h-2" />
                </div>
              </div>
            </div>
          </Card>

          {/* Details Tabs */}
          <Card className="shadow-soft animate-slide-up">
            <Tabs defaultValue="matching" className="w-full">
              <TabsList className="w-full justify-start rounded-none border-b bg-transparent p-0">
                <TabsTrigger 
                  value="matching" 
                  className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent"
                >
                  <CheckCircle2 className="w-4 h-4 mr-2" />
                  Совпадающие навыки
                </TabsTrigger>
                <TabsTrigger 
                  value="missing"
                  className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent"
                >
                  <AlertCircle className="w-4 h-4 mr-2" />
                  Недостающие навыки
                </TabsTrigger>
                <TabsTrigger 
                  value="recommendations"
                  className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent"
                >
                  <Lightbulb className="w-4 h-4 mr-2" />
                  Рекомендации AI
                </TabsTrigger>
              </TabsList>

              <TabsContent value="matching" className="p-6 space-y-4">
                <p className="text-muted-foreground mb-4">
                  Эти навыки из вашего резюме соответствуют требованиям вакансии
                </p>
                <div className="grid gap-3">
                  {matchingSkills.map((skill, index) => (
                    <div key={index} className="flex items-center justify-between p-4 rounded-lg bg-success/5 border border-success/20">
                      <span className="font-medium">{skill.name}</span>
                      <Badge variant={skill.level === "high" ? "default" : "secondary"} className="bg-success text-success-foreground">
                        {skill.level === "high" ? "Отлично" : "Хорошо"}
                      </Badge>
                    </div>
                  ))}
                </div>
              </TabsContent>

              <TabsContent value="missing" className="p-6 space-y-4">
                <p className="text-muted-foreground mb-4">
                  Эти навыки требуются для вакансии, но не указаны в вашем резюме
                </p>
                <div className="grid gap-3">
                  {missingSkills.map((skill, index) => (
                    <div key={index} className="flex items-center justify-between p-4 rounded-lg bg-warning/5 border border-warning/20">
                      <span className="font-medium">{skill.name}</span>
                      <Badge variant={skill.importance === "high" ? "destructive" : "secondary"} className="bg-warning text-warning-foreground">
                        {skill.importance === "high" ? "Важно" : "Желательно"}
                      </Badge>
                    </div>
                  ))}
                </div>
              </TabsContent>

              <TabsContent value="recommendations" className="p-6 space-y-4">
                <p className="text-muted-foreground mb-4">
                  Рекомендации AI для улучшения вашего отклика
                </p>
                <div className="grid gap-3">
                  {recommendations.map((rec, index) => (
                    <div key={index} className="flex gap-3 p-4 rounded-lg bg-primary/5 border border-primary/20">
                      <Lightbulb className="w-5 h-5 text-primary flex-shrink-0 mt-0.5" />
                      <span>{rec}</span>
                    </div>
                  ))}
                </div>
              </TabsContent>
            </Tabs>
          </Card>

          {/* Action Button */}
          <div className="flex justify-center">
            <Button
              size="lg"
              className="gradient-hero text-lg shadow-card min-w-[250px]"
              onClick={() => navigate('/results')}
            >
              Сгенерировать документы
              <ArrowRight className="ml-2 h-5 w-5" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Analysis;