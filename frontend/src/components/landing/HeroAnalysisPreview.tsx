import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Sparkles, FileText, Target, Lightbulb } from "lucide-react";

const matchScore = 74;

const recommendationPoints = [
  { label: "A/B тестирование", value: 82 },
  { label: "EdTech опыт", value: 56 },
  { label: "Growth гипотезы", value: 68 }
];

export const HeroAnalysisPreview = () => {
  return (
    <Card className="relative overflow-hidden border-0 shadow-card bg-gradient-to-br from-white/90 via-white/95 to-secondary/60">
      <div className="absolute -top-16 -right-10 h-40 w-40 rounded-full bg-gradient-hero opacity-60 blur-3xl" />
      <div className="space-y-6 relative z-10 p-6 md:p-8">
        <div className="flex items-center gap-3">
          <div className="h-12 w-12 rounded-xl bg-primary/10 flex items-center justify-center">
            <Sparkles className="h-6 w-6 text-primary" />
          </div>
          <div>
            <p className="text-sm text-muted-foreground">AI-анализ</p>
            <p className="text-lg font-semibold">EdTon · Product Manager</p>
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <Card className="border-dashed border-primary/30 bg-background/80 p-4">
            <div className="flex items-center gap-3">
              <FileText className="h-5 w-5 text-primary" />
              <div>
                <p className="text-sm text-muted-foreground">Резюме</p>
                <p className="text-sm font-medium">Мария Смирнова · 2 года опыта</p>
              </div>
            </div>
            <ul className="mt-3 space-y-2 text-xs text-muted-foreground">
              <li>• Финтех продукты · SQL · Python</li>
              <li>• Управление roadmap · исследования</li>
            </ul>
          </Card>
          <Card className="border-dashed border-primary/30 bg-background/80 p-4">
            <div className="flex items-center gap-3">
              <Target className="h-5 w-5 text-primary" />
              <div>
                <p className="text-sm text-muted-foreground">Вакансия</p>
                <p className="text-sm font-medium">Lead PM · EdTech</p>
              </div>
            </div>
            <ul className="mt-3 space-y-2 text-xs text-muted-foreground">
              <li>• A/B тесты · рост retention</li>
              <li>• Экспертиза в образовании</li>
            </ul>
          </Card>
        </div>

        <div className="rounded-2xl gradient-aurora p-5 text-white shadow-soft">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-sm font-medium uppercase tracking-wider text-white/70">Совпадение профиля</p>
              <p className="mt-1 text-3xl font-semibold">{matchScore}%</p>
            </div>
            <Badge variant="secondary" className="bg-white/20 text-white">
              +12% к базовому резюме
            </Badge>
          </div>
          <Progress value={matchScore} className="mt-4 h-2 bg-white/20" />
          <div className="mt-4 space-y-2 text-sm text-white/80">
            <p>✅ Совпадения: SQL, Python, Agile</p>
            <p>⚠️ Дополнить: A/B тесты, EdTech кейсы</p>
          </div>
        </div>

        <Card className="border-0 bg-background/90 p-5 shadow-soft">
          <div className="flex items-center gap-3">
            <Lightbulb className="h-5 w-5 text-primary" />
            <div>
              <p className="text-sm font-medium">Рекомендации AI</p>
              <p className="text-xs text-muted-foreground">Сфокусируйтесь на следующем</p>
            </div>
          </div>
          <div className="mt-4 grid gap-3 sm:grid-cols-3">
            {recommendationPoints.map((item) => (
              <div key={item.label} className="rounded-xl border border-border/60 bg-secondary/40 p-3">
                <p className="text-xs font-medium text-muted-foreground">{item.label}</p>
                <div className="mt-2 text-lg font-semibold text-foreground">{item.value}%</div>
                <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-secondary">
                  <div
                    className="h-full rounded-full bg-gradient-hero"
                    style={{ width: `${item.value}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </Card>
  );
};

export default HeroAnalysisPreview;
