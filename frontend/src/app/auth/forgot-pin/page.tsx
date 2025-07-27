"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2, AlertCircle, CheckCircle, ArrowLeft } from "lucide-react";
import { DumSocialLogo } from "@/components/sidebar/dum-social-logo";
import Link from "next/link";

export default function ForgotPinPage() {
  const [email, setEmail] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");

    try {
      const response = await fetch("/api/auth/request-reset", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email }),
      });

      const data = await response.json();

      if (data.success) {
        setSuccess(true);
      } else {
        setError(data.error || "Failed to send reset email");
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
              <CardTitle className="text-2xl font-playfair">Check Your Email</CardTitle>
              <CardDescription>
                We've sent a PIN reset link to your email address
              </CardDescription>
            </div>
          </CardHeader>
          
          <CardContent className="space-y-4">
            <Alert>
              <CheckCircle className="h-4 w-4" />
              <AlertDescription>
                If the email exists in our system, you'll receive a reset link shortly. 
                Please check your inbox and spam folder.
              </AlertDescription>
            </Alert>
          </CardContent>
          
          <CardFooter>
            <Link href="/auth/login" className="w-full">
              <Button variant="outline" className="w-full">
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back to Login
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
            <CardTitle className="text-2xl font-playfair">Reset Your PIN</CardTitle>
            <CardDescription>
              Enter your email address and we'll send you a reset link
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
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="Enter your email address"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
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
                  Sending Reset Link...
                </>
              ) : (
                "Send Reset Link"
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
