import type { Preview } from "@storybook/react";
import "../src/index.css";

declare module "@storybook/react" {
  interface Parameters {
    backgrounds?: {
      default?: string;
    };
  }
}

const preview: Preview = {
  parameters: {
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/
      }
    },
    backgrounds: {
      default: "light"
    },
    layout: "fullscreen",
    options: {
      storySort: {
        order: ["Landing", ["Hero Analysis Preview", "Resume Insights"]]
      }
    }
  }
};

export default preview;
