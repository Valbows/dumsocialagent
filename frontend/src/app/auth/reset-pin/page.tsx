"use client";

import { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2, AlertCircle, CheckCircle, ArrowLeft } from "lucide-react";
import { DumSocialLogo } from "@/components/sidebar/dum-social-logo";
import Link from "next/link";

export default function ResetPinPage() {
  const [newPin, setNewPin] = useState("");
  const [confirmPin, setConfirmPin] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [token, setToken] = useState("");
  
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    const tokenParam = searchParams.get("token");
    if (tokenParam) {
      setToken(tokenParam);
    } else {
      setError("Invalid reset link. Please request a new one.");
    }
  }, [searchParams]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");

    // Validate PIN format
    if (!/^\d{4,6}$/.test(newPin)) {
      setError("PIN must be 4-6 digits");
      setIsLoading(false);
      return;
    }

    // Validate PIN confirmation
    if (newPin !== confirmPin) {
      setError("PINs do not match");
      setIsLoading(false);
      return;
    }

    try {
      const response = await fetch("/api/auth/reset-pin", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ token, new_pin: newPin }),
      });

      const data = await response.json();

      if (data.success) {
        setSuccess(true);
        // Redirect to login after 3 seconds
        setTimeout(() => {
          router.push("/auth/login");
        }, 3000);
      } else {
        setError(data.error || "Failed to reset PIN");
      }
    } catch (err) {
      setError("Network error. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background to-secondary/20 p-4">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center space-y-4">
            <div className="flex justify-center">
              <DumSocialLogo className="h-12 w-auto" />
            </div>
            <div>
              <CardTitle className="text-2xl font-playfair">PIN Reset Successful</CardTitle>
              <CardDescription>
                Your PIN has been updated successfully
              </CardDescription>
            </div>
          </CardHeader>
          
          <CardContent className="space-y-4">
            <Alert>
              <CheckCircle className="h-4 w-4" />
              <AlertDescription>
                Your PIN has been reset successfully. You will be redirected to the login page shortly.
              </AlertDescription>
            </Alert>
          </CardContent>
          
          <CardFooter>
            <Link href="/auth/login" className="w-full">
              <Button className="w-full bg-primary hover:bg-primary/90">
                Continue to Login
              </Button>
            </Link>
          </CardFooter>
        </Card>
      </div>
    );
  }

  if (!token) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background to-secondary/20 p-4">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center space-y-4">
            <div className="flex justify-center">
              <DumSocialLogo className="h-12 w-auto" />
            </div>
            <div>
              <CardTitle className="text-2xl font-playfair">Invalid Reset Link</CardTitle>
              <CardDescription>
                This reset link is invalid or has expired
              </CardDescription>
            </div>
          </CardHeader>
          
          <CardContent className="space-y-4">
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                The reset link is invalid or has expired. Please request a new one.
              </AlertDescription>
            </Alert>
          </CardContent>
          
          <CardFooter>
            <Link href="/auth/forgot-pin" className="w-full">
              <Button className="w-full bg-primary hover:bg-primary/90">
                Request New Reset Link
              </Button>
            </Link>
          </CardFooter>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background to-secondary/20 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center space-y-4">
          <div className="flex justify-center">
            <DumSocialLogo className="h-12 w-auto" />
          </div>
          <div>
            <CardTitle className="text-2xl font-playfair">Set New PIN</CardTitle>
            <CardDescription>
              Enter your new 4-6 digit PIN
            </CardDescription>
          </div>
        </CardHeader>
        
        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-4">
            {error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
            
            <div className="space-y-2">
              <Label htmlFor="newPin">New PIN</Label>
              <Input
                id="newPin"
                type="password"
                placeholder="Enter new 4-6 digit PIN"
                value={newPin}
                onChange={(e) => setNewPin(e.target.value)}
                maxLength={6}
                pattern="[0-9]*"
                required
                disabled={isLoading}
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="confirmPin">Confirm PIN</Label>
              <Input
                id="confirmPin"
                type="password"
                placeholder="Confirm your new PIN"
                value={confirmPin}
                onChange={(e) => setConfirmPin(e.target.value)}
                maxLength={6}
                pattern="[0-9]*"
                required
                disabled={isLoading}
              />
            </div>
          </CardContent>
          
          <CardFooter className="flex flex-col space-y-4">
            <Button 
              type="submit" 
              className="w-full bg-primary hover:bg-primary/90"
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Updating PIN...
                </>
              ) : (
                "Update PIN"
              )}
            </Button>
            
            <Link href="/auth/login" className="w-full">
              <Button variant="outline" className="w-full">
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back to Login
              </Button>
            </Link>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}
