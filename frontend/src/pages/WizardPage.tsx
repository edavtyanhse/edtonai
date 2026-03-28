import WizardLayout, { type WizardStep } from '@/components/WizardLayout'
import { WizardProvider } from '@/context/WizardContext'
import { useWizard } from '@/hooks'
import { Step1Resume, Step2Vacancy, Step3Analysis, Step4Improvement } from './wizard'
import { useEffect } from 'react'
import { trackBehaviorEvent } from '@/features/feedback/analytics'

import { useTranslation } from 'react-i18next'

function WizardContent() {
  const { currentStep } = useWizard()
  const { t } = useTranslation()

  useEffect(() => {
    trackBehaviorEvent('step_entered', {
      step: `step_${currentStep}`,
      properties: {
        step_number: currentStep,
      },
    })
  }, [currentStep])

  const steps: WizardStep[] = [
    { id: 1, title: t('wizard.steps.resume'), subtitle: t('wizard.steps.subtitle_parsing') },
    { id: 2, title: t('wizard.steps.vacancy'), subtitle: t('wizard.steps.subtitle_parsing') },
    { id: 3, title: t('wizard.steps.analysis'), subtitle: t('wizard.steps.subtitle_analysis') },
    {
      id: 4,
      title: t('wizard.steps.improvement'),
      subtitle: t('wizard.steps.subtitle_improvement'),
    },
  ]

  const renderStep = () => {
    switch (currentStep) {
      case 1:
        return <Step1Resume />
      case 2:
        return <Step2Vacancy />
      case 3:
        return <Step3Analysis />
      case 4:
        return <Step4Improvement />
      default:
        return <Step1Resume />
    }
  }

  return (
    <WizardLayout steps={steps} currentStep={currentStep}>
      {renderStep()}
    </WizardLayout>
  )
}

export default function WizardPage() {
  return (
    <WizardProvider>
      <WizardContent />
    </WizardProvider>
  )
}
