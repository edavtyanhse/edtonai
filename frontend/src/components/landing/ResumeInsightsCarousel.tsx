import { Card } from "@/components/ui/card";
import {
  Carousel,
  CarouselContent,
  CarouselItem,
  CarouselNext,
  CarouselPrevious
} from "@/components/ui/carousel";
import { Badge } from "@/components/ui/badge";

const insights = [
  {
    title: "Рекомендованные достижения",
    score: "+18%",
    highlight: "Добавьте кейс про рост retention на 22%",
    summary: "AI рекомендует подчеркнуть эксперимент с A/B тестами, чтобы показать продуктовое мышление.",
    accent: "#4F8EF9"
  },
  {
    title: "Советы по стилю",
    score: "92%",
    highlight: "Используйте активные глаголы и цифры",
    summary: "Мы переписали блок опыта на более динамичный, сохранив факты из исходного резюме.",
    accent: "#8B7CFB"
  },
  {
    title: "Подбор soft skills",
    score: "3 инсайта",
    highlight: "Вставьте историю про фасилитацию discovery-сессий",
    summary: "Работодателю важна командная работа — добавьте пример взаимодействия с педагогами и аналитиками.",
    accent: "#49C572"
  }
];

const InsightGlyph = ({ accent }: { accent: string }) => (
  <svg viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg" className="h-16 w-16">
    <rect x="10" y="10" width="100" height="100" rx="24" ry="24" fill={`${accent}1A`} stroke={accent} strokeWidth="3" />
    <path d="M36 60C36 44 48 32 64 32C80 32 92 44 92 60C92 76 80 88 64 88C58 88 52.4 86 48 82" stroke={accent} strokeWidth="5" strokeLinecap="round" fill="none" />
    <text x="60" y="66" textAnchor="middle" fontFamily="'Inter', sans-serif" fontWeight="700" fontSize="22" fill={accent}>
      AI
    </text>
    <path d="M50 98 L68 98" stroke={accent} strokeWidth="4" strokeLinecap="round" />
  </svg>
);

export const ResumeInsightsCarousel = () => {
  return (
    <Carousel className="relative" opts={{ align: "start", loop: true }}>
      <CarouselContent>
        {insights.map((item) => (
          <CarouselItem key={item.title} className="md:basis-1/2 lg:basis-1/3">
            <Card className="h-full border-0 bg-gradient-to-br from-white via-white to-secondary/30 p-6 shadow-soft">
              <div className="flex items-start justify-between gap-4">
                <div className="space-y-2">
                  <Badge className="bg-background text-foreground shadow-sm">{item.score}</Badge>
                  <h3 className="text-lg font-semibold">{item.title}</h3>
                  <p className="text-sm text-muted-foreground">{item.summary}</p>
                </div>
                <InsightGlyph accent={item.accent} />
              </div>
              <div className="mt-6 rounded-2xl border border-dashed border-primary/30 gradient-insight p-4 text-sm">
                <p className="font-medium text-foreground/90">{item.highlight}</p>
              </div>
            </Card>
          </CarouselItem>
        ))}
      </CarouselContent>
      <CarouselPrevious className="bg-background/90 shadow-card" />
      <CarouselNext className="bg-background/90 shadow-card" />
    </Carousel>
  );
};

export default ResumeInsightsCarousel;
