import { useMemo } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { AlertCircle, Check, CreditCard, Loader2, RefreshCw, ShieldCheck } from 'lucide-react'
import { Button } from '@/components'
import {
  createCheckoutSession,
  getBillingAccount,
  getBillingPlans,
  type BillingPlan,
  type BillingPrice,
  type UsageFeature,
} from '@/api'

const PLAN_ORDER = ['free', 'paid_weekly', 'paid_monthly', 'paid_quarterly']
const CHECKOUT_IDEMPOTENCY_PREFIX = 'checkout'

function formatMoney(price?: BillingPrice): string {
  if (!price) {
    return 'Цена недоступна'
  }

  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: price.currency,
    maximumFractionDigits: 0,
  }).format(price.amount_minor / 100)
}

function formatPeriod(period: string): string {
  const periods: Record<string, string> = {
    free: 'бесплатно',
    week: 'за неделю',
    month: 'за месяц',
    quarter: 'за 3 месяца',
  }
  return periods[period] ?? period
}

function formatDate(value?: string | null): string {
  if (!value) {
    return 'не задано'
  }
  return new Intl.DateTimeFormat('ru-RU', {
    day: '2-digit',
    month: 'long',
    year: 'numeric',
  }).format(new Date(value))
}

function generateIdempotencyKey(planCode: string): string {
  const randomId =
    typeof crypto !== 'undefined' && 'randomUUID' in crypto
      ? crypto.randomUUID()
      : `${Date.now()}-${Math.random().toString(16).slice(2)}`
  return `${CHECKOUT_IDEMPOTENCY_PREFIX}:${planCode}:${randomId}`
}

function getPrimaryPrice(plan: BillingPlan): BillingPrice | undefined {
  return plan.prices.find((price) => price.provider === 'tbank') ?? plan.prices[0]
}

function sortPlans(plans: BillingPlan[]): BillingPlan[] {
  return [...plans].sort((left, right) => {
    const leftIndex = PLAN_ORDER.indexOf(left.code)
    const rightIndex = PLAN_ORDER.indexOf(right.code)
    const normalizedLeft = leftIndex === -1 ? PLAN_ORDER.length : leftIndex
    const normalizedRight = rightIndex === -1 ? PLAN_ORDER.length : rightIndex
    return normalizedLeft - normalizedRight
  })
}

function describeEntitlement(limit: number | null | undefined): string {
  if (limit === null || limit === undefined) {
    return 'AI операции без лимита'
  }
  return `${limit} AI операций`
}

function UsageRow({ item }: { item: UsageFeature }) {
  const limitLabel = item.limit_value === null || item.limit_value === undefined ? 'без лимита' : item.limit_value
  const remainingLabel =
    item.remaining === null || item.remaining === undefined ? 'без лимита' : item.remaining

  return (
    <div className="flex flex-col gap-2 rounded-lg border border-app-border bg-app-surface px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <div className="font-medium text-app-text">{item.feature_code}</div>
        <div className="text-sm text-app-text-muted">
          Период до {formatDate(item.period_end)}
        </div>
      </div>
      <div className="text-sm text-app-text-muted sm:text-right">
        <div>Использовано: {item.used}</div>
        <div>
          Осталось: {remainingLabel} из {limitLabel}
        </div>
      </div>
    </div>
  )
}

export default function BillingPage() {
  const queryClient = useQueryClient()
  const plansQuery = useQuery({
    queryKey: ['billing', 'plans'],
    queryFn: ({ signal }) => getBillingPlans(signal),
  })
  const accountQuery = useQuery({
    queryKey: ['billing', 'account'],
    queryFn: ({ signal }) => getBillingAccount(signal),
  })

  const checkoutMutation = useMutation({
    mutationFn: (planCode: string) =>
      createCheckoutSession({
        plan_code: planCode,
        idempotency_key: generateIdempotencyKey(planCode),
      }),
    onSuccess: (checkout) => {
      if (checkout.payment_url) {
        window.location.assign(checkout.payment_url)
        return
      }
      queryClient.invalidateQueries({ queryKey: ['billing', 'account'] })
    },
  })

  const plans = useMemo(() => sortPlans(plansQuery.data?.items ?? []), [plansQuery.data])
  const paidPlans = plans.filter((plan) => plan.code !== 'free')
  const freePlan = plans.find((plan) => plan.code === 'free')
  const currentSubscription = accountQuery.data?.subscription
  const currentPlanCode = currentSubscription?.plan_code ?? 'free'
  const isLoading = plansQuery.isLoading || accountQuery.isLoading
  const isRefetching = plansQuery.isFetching || accountQuery.isFetching
  const queryError = plansQuery.error || accountQuery.error
  const checkoutError = checkoutMutation.error

  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-app-accent">
            Подписка
          </p>
          <h1 className="mt-2 text-3xl font-bold text-app-text">Тарифы и доступ</h1>
          <p className="mt-3 max-w-2xl text-app-text-muted">
            Выберите период доступа. Цена, лимиты и статус берутся только с backend.
          </p>
        </div>
        <Button
          variant="secondary"
          onClick={() => {
            plansQuery.refetch()
            accountQuery.refetch()
          }}
          loading={isRefetching && !isLoading}
          icon={<RefreshCw />}
        >
          Обновить
        </Button>
      </div>

      {queryError && (
        <div className="flex items-start gap-3 rounded-lg border border-app-danger/30 bg-app-danger-soft px-4 py-3 text-app-danger">
          <AlertCircle className="mt-0.5 h-5 w-5 shrink-0" />
          <div>
            <div className="font-semibold">Не удалось загрузить подписку</div>
            <div className="text-sm">Попробуйте обновить страницу или повторить запрос позже.</div>
          </div>
        </div>
      )}

      {checkoutError && (
        <div className="flex items-start gap-3 rounded-lg border border-app-warning/40 bg-app-warning-soft px-4 py-3 text-app-warning">
          <AlertCircle className="mt-0.5 h-5 w-5 shrink-0" />
          <div>
            <div className="font-semibold">Оплата временно недоступна</div>
            <div className="text-sm">
              Если платежный провайдер еще не включен, оформление станет доступно после тестового запуска.
            </div>
          </div>
        </div>
      )}

      <section className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_360px]">
        <div className="rounded-lg border border-app-border bg-app-surface px-5 py-5">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-app-accent-border bg-app-accent-soft text-app-accent">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-app-text">Текущий доступ</h2>
              <p className="text-sm text-app-text-muted">Статус и лимиты синхронизируются с backend.</p>
            </div>
          </div>

          {isLoading ? (
            <div className="mt-6 flex items-center gap-2 text-app-text-muted">
              <Loader2 className="h-4 w-4 animate-spin" />
              Загружаем данные подписки
            </div>
          ) : (
            <div className="mt-6 space-y-4">
              <div className="grid gap-3 sm:grid-cols-3">
                <div className="rounded-lg border border-app-border bg-app-surface-muted px-4 py-3">
                  <div className="text-sm text-app-text-muted">План</div>
                  <div className="mt-1 font-semibold text-app-text">{currentPlanCode}</div>
                </div>
                <div className="rounded-lg border border-app-border bg-app-surface-muted px-4 py-3">
                  <div className="text-sm text-app-text-muted">Статус</div>
                  <div className="mt-1 font-semibold text-app-text">
                    {currentSubscription?.status ?? 'free'}
                  </div>
                </div>
                <div className="rounded-lg border border-app-border bg-app-surface-muted px-4 py-3">
                  <div className="text-sm text-app-text-muted">Доступ до</div>
                  <div className="mt-1 font-semibold text-app-text">
                    {formatDate(currentSubscription?.current_period_end)}
                  </div>
                </div>
              </div>

              {accountQuery.data?.usage.length ? (
                <div className="space-y-3">
                  {accountQuery.data.usage.map((item) => (
                    <UsageRow key={item.feature_code} item={item} />
                  ))}
                </div>
              ) : (
                <div className="rounded-lg border border-app-border bg-app-surface-muted px-4 py-3 text-sm text-app-text-muted">
                  Usage появится после первой AI операции.
                </div>
              )}
            </div>
          )}
        </div>

        {freePlan && (
          <div className="rounded-lg border border-app-border bg-app-surface px-5 py-5">
            <h2 className="text-lg font-semibold text-app-text">Бесплатный доступ</h2>
            <p className="mt-2 text-sm text-app-text-muted">
              {freePlan.description ?? 'Базовый лимит для знакомства с сервисом.'}
            </p>
            <div className="mt-5 space-y-2">
              {freePlan.entitlements.map((entitlement) => (
                <div key={entitlement.feature_code} className="flex items-center gap-2 text-sm text-app-text">
                  <Check className="h-4 w-4 text-app-success" />
                  {describeEntitlement(entitlement.limit_value)}
                </div>
              ))}
            </div>
          </div>
        )}
      </section>

      <section>
        <h2 className="text-xl font-semibold text-app-text">Платные периоды</h2>
        <div className="mt-4 grid gap-4 md:grid-cols-3">
          {paidPlans.map((plan) => {
            const price = getPrimaryPrice(plan)
            const isCurrent = currentPlanCode === plan.code
            const isPending = checkoutMutation.isPending && checkoutMutation.variables === plan.code
            return (
              <article
                key={plan.code}
                className={`flex min-h-[280px] flex-col rounded-lg border bg-app-surface px-5 py-5 ${
                  isCurrent ? 'border-app-accent shadow-lg shadow-brand-500/10' : 'border-app-border'
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h3 className="text-lg font-semibold text-app-text">{plan.title}</h3>
                    <p className="mt-1 text-sm text-app-text-muted">
                      {formatPeriod(plan.billing_period)}
                    </p>
                  </div>
                  {isCurrent && (
                    <span className="rounded-full border border-app-accent-border bg-app-accent-soft px-3 py-1 text-xs font-semibold text-app-accent">
                      текущий
                    </span>
                  )}
                </div>

                <div className="mt-5">
                  <div className="text-3xl font-bold text-app-text">{formatMoney(price)}</div>
                  <p className="mt-2 text-sm text-app-text-muted">
                    {plan.description ?? 'Доступ ко всем AI операциям на выбранный период.'}
                  </p>
                </div>

                <div className="mt-5 flex-1 space-y-2">
                  {plan.entitlements.map((entitlement) => (
                    <div key={entitlement.feature_code} className="flex items-center gap-2 text-sm text-app-text">
                      <Check className="h-4 w-4 text-app-success" />
                      {describeEntitlement(entitlement.limit_value)}
                    </div>
                  ))}
                </div>

                <Button
                  className="mt-6 w-full"
                  onClick={() => checkoutMutation.mutate(plan.code)}
                  disabled={!price || isPending}
                  loading={isPending}
                  icon={<CreditCard />}
                >
                  Оплатить
                </Button>
              </article>
            )
          })}
        </div>
      </section>
    </div>
  )
}
