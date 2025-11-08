import type { Meta, StoryObj } from "@storybook/react";
import { HeroAnalysisPreview } from "@/components/landing/HeroAnalysisPreview";

const meta: Meta<typeof HeroAnalysisPreview> = {
  title: "Landing/Hero Analysis Preview",
  component: HeroAnalysisPreview,
  parameters: {
    docs: {
      description: {
        component: "Демонстрация AI-панели с результатом анализа совпадения резюме и вакансии."
      }
    }
  },
  decorators: [
    (Story) => (
      <div className="mx-auto max-w-3xl px-8 py-10 bg-secondary/40">
        <Story />
      </div>
    )
  ]
};

export default meta;

type Story = StoryObj<typeof meta>;

export const Default: Story = {};
