import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { apiFetch, ApiError } from '@/lib/api'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card'
import { ShieldCheckIcon } from 'lucide-react'

const OTP_TTL_SECONDS = 300
const OTP_MAX_ATTEMPTS = 5

export default function VerifyPage() {
  const navigate = useNavigate()
  const [code, setCode] = useState(['', '', '', '', '', ''])
  const [attempts, setAttempts] = useState(0)
  const [expiryTime, setExpiryTime] = useState<number>(Date.now() + OTP_TTL_SECONDS * 1000)
  const [timeLeft, setTimeLeft] = useState(OTP_TTL_SECONDS)
  const [errorMessage, setErrorMessage] = useState('')
  const inputRefs = useRef<(HTMLInputElement | null)[]>([])

  useEffect(() => {
    setExpiryTime(Date.now() + OTP_TTL_SECONDS * 1000)
    setTimeLeft(OTP_TTL_SECONDS)
  }, [])

  useEffect(() => {
    const interval = setInterval(() => {
      const remaining = Math.max(0, Math.ceil((expiryTime - Date.now()) / 1000))
      setTimeLeft(remaining)
    }, 200)
    return () => clearInterval(interval)
  }, [expiryTime])

  const mutation = useMutation({
    mutationFn: (otpCode: string) =>
      apiFetch<{ status: string }>('/auth/verify', {
        method: 'POST',
        body: JSON.stringify({ code: otpCode }),
      }),
    onSuccess: () => {
      navigate('/')
    },
    onError: (err) => {
      setAttempts((prev) => prev + 1)
      if (err instanceof ApiError) {
        if (err.status === 429) {
          setErrorMessage('Too many attempts. Request a new code.')
        } else if (err.message === 'Code expired.') {
          setErrorMessage('Code expired. Request a new code.')
        } else {
          setErrorMessage(err.message)
        }
      } else {
        setErrorMessage('Verification failed.')
      }
      setCode(['', '', '', '', '', ''])
      inputRefs.current[0]?.focus()
    },
  })

  const handleInput = (index: number, value: string) => {
    if (!/^\d*$/.test(value)) return
    const next = [...code]
    next[index] = value.slice(-1)
    setCode(next)

    if (value && index < 5) {
      inputRefs.current[index + 1]?.focus()
    }

    const combined = next.join('')
    if (combined.length === 6) {
      setErrorMessage('')
      mutation.mutate(combined)
    }
  }

  const handleKeyDown = (index: number, e: React.KeyboardEvent) => {
    if (e.key === 'Backspace' && !code[index] && index > 0) {
      inputRefs.current[index - 1]?.focus()
    }
  }

  const handlePaste = (e: React.ClipboardEvent) => {
    e.preventDefault()
    const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6)
    const next = [...code]
    for (let i = 0; i < pasted.length; i++) {
      next[i] = pasted[i]
    }
    setCode(next)
    if (pasted.length === 6) {
      setErrorMessage('')
      mutation.mutate(pasted)
    } else {
      inputRefs.current[Math.min(pasted.length, 5)]?.focus()
    }
  }

  const remainingAttempts = OTP_MAX_ATTEMPTS - attempts
  const isExpired = timeLeft <= 0

  const resend = () => {
    navigate('/login')
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-muted/30">
      <Card className="w-full max-w-sm">
        <CardHeader className="text-center">
          <div className="mx-auto mb-2 flex size-10 items-center justify-center rounded-full bg-primary/10">
            <ShieldCheckIcon className="size-5 text-primary" />
          </div>
          <CardTitle>Verify Code</CardTitle>
          <CardDescription>
            Enter the 6-digit code sent to your email.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col gap-4">
            <div className="flex justify-center gap-2" onPaste={handlePaste}>
              {code.map((digit, i) => (
                <Input
                  key={i}
                  ref={(el) => { inputRefs.current[i] = el }}
                  type="text"
                  inputMode="numeric"
                  maxLength={1}
                  value={digit}
                  onChange={(e) => handleInput(i, e.target.value)}
                  onKeyDown={(e) => handleKeyDown(i, e)}
                  disabled={mutation.isPending}
                  className="size-12 text-center text-lg"
                  autoFocus={i === 0}
                />
              ))}
            </div>

            <div className="text-center text-sm text-muted-foreground">
              {isExpired ? (
                <span className="text-destructive">Code expired.</span>
              ) : (
                <span>
                  Expires in {Math.floor(timeLeft / 60)}:
                  {String(timeLeft % 60).padStart(2, '0')}
                </span>
              )}
            </div>

            {remainingAttempts <= 2 && remainingAttempts > 0 && (
              <p className="text-center text-sm text-amber-600">
                {remainingAttempts} attempt{remainingAttempts !== 1 ? 's' : ''} remaining
              </p>
            )}

            {errorMessage && (
              <p className="text-center text-sm text-destructive">{errorMessage}</p>
            )}

            {mutation.isPending && (
              <p className="text-center text-sm text-muted-foreground">Verifying...</p>
            )}
          </div>
        </CardContent>
        <CardFooter className="flex flex-col gap-2">
          <Button
            type="button"
            variant="outline"
            className="w-full"
            onClick={resend}
          >
            Request New Code
          </Button>
        </CardFooter>
      </Card>
    </div>
  )
}
