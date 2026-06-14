import { useQuery } from '@tanstack/react-query'
import { CheckCircle2, Loader2, RefreshCw } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Button } from '@/components'
import { getBillingAccount } from '@/api'

export default function BillingSuccessPage() {
  const accountQuery = useQuery({
    queryKey: ['billing', 'account'],
    queryFn: ({ signal }) => getBillingAccount(signal),
    refetchInterval: (query) => {
      const subscription = query.state.data?.subscription
      return subscription?.status === 'active' ? false : 5000
    },
  })

  const subscription = accountQuery.data?.subscription
  const isActive = subscription?.status === 'active'

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div className="rounded-lg border border-app-border bg-app-surface px-6 py-7">
        <div className="flex items-start gap-4">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg border border-app-success/30 bg-app-success-soft text-app-success">
            {isActive ? <CheckCircle2 className="h-6 w-6" /> : <Loader2 className="h-6 w-6 animate-spin" />}
          </div>
          <div>
            <h1 className="text-2xl font-bold text-app-text">
              {isActive ? 'Подписка активирована' : 'Оплата проверяется'}
            </h1>
            <p className="mt-3 text-app-text-muted">
              Доступ включается только после подтверждения платежа от Т-Банка. Эта страница сама не
              активирует подписку.
            </p>
          </div>
        </div>

        <div className="mt-6 rounded-lg border border-app-border bg-app-surface-muted px-4 py-3 text-sm text-app-text-muted">
          <div>Статус: {subscription?.status ?? 'ожидаем подтверждение'}</div>
          <div>План: {subscription?.plan_code ?? 'пока не назначен'}</div>
        </div>

        <div className="mt-6 flex flex-col gap-3 sm:flex-row">
          <Button
            variant="secondary"
            onClick={() => accountQuery.refetch()}
            loading={accountQuery.isFetching}
            icon={<RefreshCw />}
          >
            Проверить статус
          </Button>
          <Link
            to="/billing"
            className="inline-flex items-center justify-center rounded-lg border border-app-border bg-app-surface px-4 py-2 text-sm font-medium text-app-text hover:bg-app-surface-muted"
          >
            К подписке
          </Link>
        </div>
      </div>
    </div>
  )
}
