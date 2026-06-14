import { AlertCircle, CreditCard } from 'lucide-react'
import { Link } from 'react-router-dom'

export default function BillingCancelPage() {
  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div className="rounded-lg border border-app-border bg-app-surface px-6 py-7">
        <div className="flex items-start gap-4">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg border border-app-warning/40 bg-app-warning-soft text-app-warning">
            <AlertCircle className="h-6 w-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-app-text">Оплата не завершена</h1>
            <p className="mt-3 text-app-text-muted">
              Платеж был отменен или не прошел. Подписка не активирована, детали платежной сессии
              не отображаются в интерфейсе.
            </p>
          </div>
        </div>

        <div className="mt-6 flex flex-col gap-3 sm:flex-row">
          <Link
            to="/billing"
            className="inline-flex items-center justify-center gap-2 rounded-lg bg-app-accent px-4 py-2 text-sm font-medium text-white hover:bg-app-accent-hover"
          >
            <CreditCard className="h-4 w-4" />
            Вернуться к тарифам
          </Link>
          <Link
            to="/workspace"
            className="inline-flex items-center justify-center rounded-lg border border-app-border bg-app-surface px-4 py-2 text-sm font-medium text-app-text hover:bg-app-surface-muted"
          >
            В рабочее пространство
          </Link>
        </div>
      </div>
    </div>
  )
}
