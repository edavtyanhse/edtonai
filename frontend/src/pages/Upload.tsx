import { useState, useMemo } from "react";
import type { ChangeEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { Upload as UploadIcon, FileText, Sparkles, ArrowRight, Link2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/hooks/use-toast";
import { api, type AnalyzeReq } from "@/lib/api";
import { saveAnalysisSession } from "@/lib/session";

const Upload = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [resumeText, setResumeText] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [targetRole, setTargetRole] = useState("");
  const [isParsingFile, setIsParsingFile] = useState(false);

  const analyzeMutation = useMutation({
    mutationFn: (payload: AnalyzeReq) => api.analyze(payload),
    onSuccess: (data, variables) => {
      saveAnalysisSession({
        request: variables,
        response: data,
      });
      toast({
        title: "Анализ завершён",
        description: "Мы нашли ключевые совпадения и рекомендации",
      });
      navigate("/analysis");
    },
    onError: (error: unknown) => {
      const message = error instanceof Error ? error.message : "Не удалось выполнить анализ";
      toast({
        title: "Ошибка анализа",
        description: message,
        variant: "destructive",
      });
    },
  });

  const resumeCharacters = useMemo(() => resumeText.trim().length, [resumeText]);

  const handleFileChange = async (event: ChangeEvent<HTMLInputElement>) => {
    if (!event.target.files || !event.target.files[0]) {
      return;
    }

    const file = event.target.files[0];
    setResumeFile(file);

    try {
      setIsParsingFile(true);
      const text = await api.parseFile(file);
      setResumeText(text);
      toast({
        title: "Файл распознан",
        description: `${file.name} успешно преобразован в текст`,
      });
    } catch (error) {
      console.error("Failed to parse resume file", error);
      const message =
        error instanceof Error ? error.message : "Вставьте текст резюме вручную ниже";
      toast({
        title: "Не удалось распознать файл",
        description: message,
        variant: "destructive",
      });
    } finally {
      setIsParsingFile(false);
    }
  };

  const handleAnalyze = () => {
    if (!resumeText.trim()) {
      toast({
        title: "Добавьте резюме",
        description: "Вставьте текст или загрузите файл с резюме",
        variant: "destructive",
      });
      return;
    }
    if (!jobDescription.trim()) {
      toast({
        title: "Добавьте вакансию",
        description: "Необходимо вставить текст вакансии",
        variant: "destructive",
      });
      return;
    }

    const payload: AnalyzeReq = {
      resume_text: resumeText,
      vacancy_text: jobDescription,
      role: targetRole || undefined,
    };

    analyzeMutation.mutate(payload);
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
              <div className="w-10 h-10 rounded-full gradient-hero flex items-center justify-center text-primary-foreground font-semibold">
                1
              </div>
              <span className="text-sm font-medium">Загрузка</span>
            </div>
            <div className="flex-1 h-0.5 bg-border mx-4" />
            <div className="flex flex-col items-center gap-2">
              <div className="w-10 h-10 rounded-full bg-secondary flex items-center justify-center text-muted-foreground font-semibold">
                2
              </div>
              <span className="text-sm text-muted-foreground">Анализ</span>
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

        {/* Upload Section */}
        <div className="max-w-4xl mx-auto space-y-8">
          <div className="text-center space-y-2 animate-fade-in">
            <h1 className="text-3xl md:text-4xl font-bold">Загрузите данные для анализа</h1>
            <p className="text-muted-foreground text-lg">
              Загрузите своё резюме и добавьте текст вакансии
            </p>
          </div>

          {/* Resume Upload */}
          <Card className="p-8 shadow-soft animate-slide-up">
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <FileText className="w-5 h-5 text-primary" />
                <h2 className="text-xl font-semibold">Загрузите своё резюме</h2>
              </div>
              <div className="border-2 border-dashed rounded-lg p-8 text-center hover:border-primary transition-colors cursor-pointer">
                <input
                  type="file"
                  id="resume-upload"
                  className="hidden"
                  accept=".pdf,.docx,.doc,.txt"
                  onChange={handleFileChange}
                />
                <label htmlFor="resume-upload" className="cursor-pointer space-y-4 block">
                  <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto">
                    <UploadIcon className="w-8 h-8 text-primary" />
                  </div>
                  <div>
                    <p className="text-lg font-medium">
                      {resumeFile ? resumeFile.name : "Нажмите для загрузки"}
                    </p>
                    <p className="text-sm text-muted-foreground mt-1">
                      Поддерживаются форматы: PDF, DOCX (до 10MB)
                    </p>
                  </div>
                </label>
              </div>
              {resumeFile && (
                <div className="flex items-center gap-2 p-3 bg-success/10 rounded-lg animate-fade-in">
                  <FileText className="w-5 h-5 text-success" />
                  <span className="text-sm font-medium truncate">{resumeFile.name}</span>
                </div>
              )}
            </div>
          </Card>

          {/* Job Description */}
          <Card className="p-8 shadow-soft animate-slide-up">
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <Link2 className="w-5 h-5 text-primary" />
                <h2 className="text-xl font-semibold">Добавьте вакансию</h2>
              </div>
              <div className="space-y-2">
                <Textarea
                  placeholder="Вставьте текст вакансии или ссылку на HH.ru..."
                  className="min-h-[200px] resize-none"
                  value={jobDescription}
                  onChange={(e) => setJobDescription(e.target.value)}
                />
                <p className="text-sm text-muted-foreground flex items-center gap-1">
                  <Sparkles className="w-4 h-4" />
                  Можно просто вставить ссылку на HH или текст вакансии
                </p>
              </div>
            </div>
          </Card>

          {/* Resume Text */}
          <Card className="p-8 shadow-soft animate-slide-up">
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-primary" />
                <h2 className="text-xl font-semibold">Проверьте текст резюме</h2>
              </div>
              <div className="space-y-2">
                <Label htmlFor="resume-text">Текст резюме</Label>
                <Textarea
                  id="resume-text"
                  placeholder="Вставьте сюда текст резюме, если файл не распознался"
                  className="min-h-[220px] resize-y"
                  value={resumeText}
                  onChange={(e) => setResumeText(e.target.value)}
                />
                <p className="text-xs text-muted-foreground">
                  Символов: {resumeCharacters}
                </p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="target-role">Целевая роль (необязательно)</Label>
                <Input
                  id="target-role"
                  placeholder="Например, Product Manager"
                  value={targetRole}
                  onChange={(e) => setTargetRole(e.target.value)}
                />
              </div>
            </div>
          </Card>

          {/* Action Button */}
          <div className="flex justify-center">
            <Button
              size="lg"
              className="gradient-hero text-lg shadow-card min-w-[250px]"
              onClick={handleAnalyze}
              disabled={analyzeMutation.isPending || isParsingFile}
            >
              {analyzeMutation.isPending || isParsingFile ? (
                <>
                  <Sparkles className="mr-2 h-5 w-5 animate-spin" />
                  {isParsingFile ? "Обрабатываю файл..." : "Анализирую..."}
                </>
              ) : (
                <>
                  Анализировать соответствие
                  <ArrowRight className="ml-2 h-5 w-5" />
                </>
              )}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Upload;
