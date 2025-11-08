import type { Meta, StoryObj } from "@storybook/react";
import { ResumeInsightsCarousel } from "@/components/landing/ResumeInsightsCarousel";

const meta: Meta<typeof ResumeInsightsCarousel> = {
  title: "Landing/Resume Insights",
  component: ResumeInsightsCarousel,
  parameters: {
    docs: {
      description: {
        component: "Карточки с рекомендациями по улучшению резюме после анализа EdTon.ai."
      }
    }
  },
  decorators: [
    (Story) => (
      <div className="mx-auto max-w-5xl px-8 py-10 bg-secondary/30">
        <Story />
      </div>
    )
  ]
};

export default meta;

type Story = StoryObj<typeof meta>;

export const Default: Story = {};
