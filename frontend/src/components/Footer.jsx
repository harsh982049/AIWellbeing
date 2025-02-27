// Footer component with links and credits
export default function Footer() {
    return (
      <footer className="border-t bg-background">
        <div className="container flex flex-col md:flex-row items-center justify-between py-10 md:py-6">
          <div className="flex flex-col items-center md:items-start gap-4 mb-8 md:mb-0">
            {/* Logo/Brand */}
            <div className="flex items-center gap-2">
              <div className="h-8 w-8 rounded-full bg-primary flex items-center justify-center text-primary-foreground font-bold">
                AW
              </div>
              <span className="text-lg font-bold">AI Emotional Wellbeing</span>
            </div>
            <p className="text-sm text-muted-foreground text-center md:text-left">
              Empowering emotional health through artificial intelligence.
            </p>
          </div>
  
          {/* Footer links */}
          <div className="grid grid-cols-2 md:grid-cols-3 gap-8 md:gap-12">
            <div className="flex flex-col gap-2">
              <h3 className="text-sm font-medium">Product</h3>
              <div className="flex flex-col gap-2">
                <a href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                  Features
                </a>
                <a href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                  Pricing
                </a>
                <a href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                  FAQ
                </a>
              </div>
            </div>
            <div className="flex flex-col gap-2">
              <h3 className="text-sm font-medium">Company</h3>
              <div className="flex flex-col gap-2">
                <a href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                  About
                </a>
                <a href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                  Blog
                </a>
                <a href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                  Careers
                </a>
              </div>
            </div>
            <div className="flex flex-col gap-2">
              <h3 className="text-sm font-medium">Legal</h3>
              <div className="flex flex-col gap-2">
                <a href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                  Privacy
                </a>
                <a href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                  Terms
                </a>
                <a href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                  Cookie Policy
                </a>
              </div>
            </div>
          </div>
        </div>
  
        {/* Copyright section */}
        <div className="border-t py-6">
          <div className="container flex flex-col md:flex-row items-center justify-between gap-4">
            <p className="text-xs text-muted-foreground">
              © {new Date().getFullYear()} AI Emotional Wellbeing. All rights reserved.
            </p>
            <div className="flex items-center gap-4">
              <a href="#" className="text-xs text-muted-foreground hover:text-foreground transition-colors">
                Privacy Policy
              </a>
              <a href="#" className="text-xs text-muted-foreground hover:text-foreground transition-colors">
                Terms of Service
              </a>
              <a href="#" className="text-xs text-muted-foreground hover:text-foreground transition-colors">
                Cookie Settings
              </a>
            </div>
          </div>
        </div>
      </footer>
    )
  }
  
  