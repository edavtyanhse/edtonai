/**
 * FEEDBACK FEATURE CONFIGURATION
 * 
 * Set VITE_FEEDBACK_ENABLED=false to disable feedback collection
 * To remove: Delete /src/features/feedback folder and remove imports
 */

export const FEEDBACK_CONFIG = {
  // Feature flag - set to false to disable entirely
  enabled: import.meta.env.VITE_FEEDBACK_ENABLED !== 'false',
  
  // Banner message on home page
  bannerMessage: {
    ru: 'Сейчас проводим активный сбор отзывов. Помогите нам улучшить продукт!',
    en: 'We are actively collecting feedback. Help us improve the product!',
  },
  
  // Modal titles
  modalTitle: {
    ru: 'Поделитесь впечатлениями',
    en: 'Share your feedback',
  },
  
  // Placeholder text
  placeholder: {
    ru: 'Расскажите, что вам понравилось или что можно улучшить...',
    en: 'Tell us what you liked or what could be improved...',
  },
  
  // When to show auto-popup (after analysis completion)
  showAfterAnalysis: true,
}
