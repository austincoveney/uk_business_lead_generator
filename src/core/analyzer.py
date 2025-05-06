"""
Website analyzer module using Lighthouse integration
"""

import os
import json
import time
import tempfile
import subprocess
import requests
from urllib.parse import urlparse


class WebsiteAnalyzer:
    """Website analysis with Lighthouse integration"""

    def __init__(self, use_lighthouse=True):
        """
        Initialize the analyzer

        Args:
            use_lighthouse: Whether to attempt to use Lighthouse
        """
        self.use_lighthouse = use_lighthouse
        self.lighthouse_available = (
            self._check_lighthouse() if use_lighthouse else False
        )

    def _check_lighthouse(self):
        """Check if Lighthouse is available via Chrome"""
        try:
            # First, try to check for Chrome with DevTools protocol capability
            chrome_paths = [
                # Windows
                os.path.join(
                    os.environ.get("PROGRAMFILES", "C:\\Program Files"),
                    "Google\\Chrome\\Application\\chrome.exe",
                ),
                os.path.join(
                    os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)"),
                    "Google\\Chrome\\Application\\chrome.exe",
                ),
                # macOS
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                # Linux
                "/usr/bin/google-chrome",
                "/usr/bin/chrome",
                "/usr/bin/chromium",
                "/usr/bin/chromium-browser",
            ]

            chrome_found = False
            for path in chrome_paths:
                if os.path.exists(path):
                    chrome_found = True
                    break

            if chrome_found:
                print("Chrome browser found, can use DevTools Protocol for Lighthouse")
                return True

            # Fall back to checking for standalone Lighthouse
            result = subprocess.run(
                ["lighthouse", "--version"], capture_output=True, text=True, timeout=10
            )
            return result.returncode == 0
        except:
            return False

    def analyze_website(self, url):
        """
        Analyze a website for performance, SEO, accessibility and best practices

        Args:
            url: URL of the website to analyze

        Returns:
            Dictionary with analysis results
        """
        # Initialize results with default values
        results = {
            "performance_score": 0,
            "seo_score": 0,
            "accessibility_score": 0,
            "best_practices_score": 0,
            "has_ssl": False,
            "has_mobile_viewport": False,
            "issues": [],
        }

        # Basic validation
        if not url:
            results["issues"].append("No URL provided")
            return results

        # Ensure URL has scheme
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        # First do some basic checks
        self._check_website_basics(url, results)

        # If Lighthouse is available, run it
        if self.lighthouse_available:
            lighthouse_results = self._run_lighthouse(url)
            if lighthouse_results:
                self._process_lighthouse_results(lighthouse_results, results)
        else:
            results["issues"].append("Lighthouse not available for detailed analysis")
            # Perform basic web checks as fallback
            self._perform_basic_analysis(url, results)

        # Set the priority based on results
        results["priority"] = self._calculate_priority(results)

        return results

    def _check_website_basics(self, url, results):
        """Check basic website properties"""
        try:
            # Check for SSL (https)
            results["has_ssl"] = url.startswith("https://")
            if not results["has_ssl"]:
                results["issues"].append("Website does not use SSL (https)")

                # Try checking if HTTPS is available
                https_url = (
                    "https://" + url[7:]
                    if url.startswith("http://")
                    else "https://" + url
                )
                try:
                    response = requests.head(
                        https_url, timeout=10, allow_redirects=True
                    )
                    if response.status_code < 400:
                        results["issues"].append(
                            "HTTPS is available but not used by default"
                        )
                except:
                    pass

            # Try to get the webpage
            response = requests.get(url, timeout=10)

            # Check for success
            if response.status_code >= 400:
                results["issues"].append(
                    f"Website returns HTTP status {response.status_code}"
                )
                return

            # Check for redirect to another domain
            if urlparse(response.url).netloc != urlparse(url).netloc:
                results["issues"].append(f"Website redirects to {response.url}")

            # Check for mobile viewport meta tag
            if "viewport" in response.text.lower():
                results["has_mobile_viewport"] = True
            else:
                results["issues"].append("No mobile viewport meta tag found")

            # Check page size
            page_size_kb = len(response.content) / 1024
            if page_size_kb > 5000:
                results["issues"].append(f"Page size is large ({page_size_kb:.1f} KB)")

        except requests.RequestException as e:
            results["issues"].append(f"Error accessing website: {str(e)}")
        except Exception as e:
            results["issues"].append(f"Error during basic analysis: {str(e)}")

    def _run_lighthouse(self, url):
        """Run Lighthouse analysis on a website"""
        # Create a temporary file for the output
        fd, output_path = tempfile.mkstemp(suffix=".json")
        os.close(fd)

        try:
            # Determine if we can use Chrome's DevTools Protocol for Lighthouse
            chrome_found = False
            chrome_paths = [
                # Windows
                os.path.join(
                    os.environ.get("PROGRAMFILES", "C:\\Program Files"),
                    "Google\\Chrome\\Application\\chrome.exe",
                ),
                os.path.join(
                    os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)"),
                    "Google\\Chrome\\Application\\chrome.exe",
                ),
                # macOS
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                # Linux
                "/usr/bin/google-chrome",
                "/usr/bin/chrome",
                "/usr/bin/chromium",
                "/usr/bin/chromium-browser",
            ]

            chrome_path = None
            for path in chrome_paths:
                if os.path.exists(path):
                    chrome_path = path
                    chrome_found = True
                    break

            if chrome_found:
                print(f"Using Chrome at {chrome_path} for Lighthouse analysis")
                # Use Chrome with DevTools Protocol
                lighthouse_command = [
                    chrome_path,
                    "--headless",
                    "--disable-gpu",
                    "--remote-debugging-port=9222",
                    "--enable-automation",
                    "--no-sandbox",
                    f"--user-data-dir={tempfile.mkdtemp()}",
                    f"--dump-dom={url}",
                    "--run-lighthouse",
                ]

                try:
                    # Start Chrome with DevTools Protocol
                    chrome_process = subprocess.Popen(
                        lighthouse_command,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                    )

                    # Wait a moment for Chrome to start
                    time.sleep(5)

                    # Run Lighthouse via npx
                    lighthouse_npx_command = [
                        "npx",
                        "lighthouse",
                        url,
                        "--output=json",
                        f"--output-path={output_path}",
                        "--chrome-flags=--headless",
                        "--only-categories=performance,accessibility,best-practices,seo",
                    ]

                    subprocess.run(lighthouse_npx_command, timeout=60, check=False)

                    # Kill the Chrome process
                    try:
                        chrome_process.terminate()
                    except:
                        pass

                except Exception as e:
                    print(f"Error using Chrome DevTools for Lighthouse: {e}")
                    # Fall back to standalone Lighthouse
                    pass

            # If we don't have Chrome or the Chrome approach failed, try standalone Lighthouse
            if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
                print("Falling back to standalone Lighthouse")
                # Run Lighthouse with minimal output categories
                lighthouse_command = [
                    "lighthouse",
                    url,
                    "--chrome-flags=--headless --no-sandbox --disable-gpu",
                    "--output=json",
                    "--output-path=" + output_path,
                    "--only-categories=performance,accessibility,best-practices,seo",
                    "--quiet",
                ]

                # Run the command with a timeout
                subprocess.run(
                    lighthouse_command,
                    capture_output=True,
                    timeout=60,  # 60 second timeout
                )

            # Check if the output file exists and has content
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                # Read and parse the JSON output
                with open(output_path, "r") as f:
                    lighthouse_data = json.load(f)

                return lighthouse_data
            else:
                print("Lighthouse didn't generate output")
                return None

        except subprocess.TimeoutExpired:
            print("Lighthouse timed out")
            return None
        except Exception as e:
            print(f"Error running Lighthouse: {e}")
            return None
        finally:
            # Clean up the temporary file
            if os.path.exists(output_path):
                os.unlink(output_path)

    def _process_lighthouse_results(self, lighthouse_data, results):
        """Process Lighthouse results into our format"""
        try:
            # Extract category scores
            categories = lighthouse_data.get("categories", {})

            if "performance" in categories:
                results["performance_score"] = int(
                    categories["performance"]["score"] * 100
                )

            if "accessibility" in categories:
                results["accessibility_score"] = int(
                    categories["accessibility"]["score"] * 100
                )

            if "best-practices" in categories:
                results["best_practices_score"] = int(
                    categories["best-practices"]["score"] * 100
                )

            if "seo" in categories:
                results["seo_score"] = int(categories["seo"]["score"] * 100)

            # Extract important audits and issues
            audits = lighthouse_data.get("audits", {})

            # Performance issues
            if "largest-contentful-paint" in audits:
                lcp = audits["largest-contentful-paint"]
                if lcp.get("score", 1) < 0.5:
                    results["issues"].append(
                        f"Slow content loading (LCP: {lcp.get('displayValue')})"
                    )

            if "total-blocking-time" in audits:
                tbt = audits["total-blocking-time"]
                if tbt.get("score", 1) < 0.5:
                    results["issues"].append(
                        f"Poor interactivity (TBT: {tbt.get('displayValue')})"
                    )

            if "cumulative-layout-shift" in audits:
                cls = audits["cumulative-layout-shift"]
                if cls.get("score", 1) < 0.5:
                    results["issues"].append(
                        f"Layout shifts during loading (CLS: {cls.get('displayValue')})"
                    )

            # SEO issues
            if "meta-description" in audits:
                if audits["meta-description"].get("score", 1) < 0.5:
                    results["issues"].append("Missing meta description")

            if "document-title" in audits:
                if audits["document-title"].get("score", 1) < 0.5:
                    results["issues"].append("Missing or poor document title")

            # Additional SEO audits
            if "link-text" in audits:
                if audits["link-text"].get("score", 1) < 0.5:
                    results["issues"].append("Poor or generic link text")

            if "hreflang" in audits:
                if audits["hreflang"].get("score", 1) < 0.5:
                    results["issues"].append("Incorrect hreflang links")

            if "canonical" in audits:
                if audits["canonical"].get("score", 1) < 0.5:
                    results["issues"].append("Missing canonical link")

            if "robots-txt" in audits:
                if audits["robots-txt"].get("score", 1) < 0.5:
                    results["issues"].append("Problems with robots.txt")

            if "structured-data" in audits and "score" in audits["structured-data"]:
                if audits["structured-data"].get("score", 1) < 0.5:
                    results["issues"].append("Missing structured data")

            # Accessibility issues
            if "color-contrast" in audits:
                if audits["color-contrast"].get("score", 1) < 0.5:
                    results["issues"].append("Poor color contrast for text")

            if "image-alt" in audits:
                if audits["image-alt"].get("score", 1) < 0.5:
                    results["issues"].append("Images missing alt text")

            # Best Practices issues
            if "is-on-https" in audits:
                if audits["is-on-https"].get("score", 1) < 0.5:
                    results["issues"].append("Not using HTTPS")

            if "doctype" in audits:
                if audits["doctype"].get("score", 1) < 0.5:
                    results["issues"].append("Missing doctype")

        except Exception as e:
            results["issues"].append(f"Error processing Lighthouse results: {str(e)}")

    def _perform_basic_analysis(self, url, results):
        """Perform basic analysis as a fallback when Lighthouse is not available"""
        try:
            # Get the webpage
            response = requests.get(url, timeout=10)
            html = response.text.lower()

            # Check response headers
            headers = response.headers

            # Performance checks
            if len(response.content) > 1000000:  # 1MB
                results["issues"].append("Large page size")
                results["performance_score"] = 50
            else:
                results["performance_score"] = 70

            # SEO checks
            results["seo_score"] = 60  # Default

            # Check for title
            if "<title>" not in html or "<title></title>" in html:
                results["issues"].append("Missing page title")
                results["seo_score"] = max(30, results["seo_score"] - 30)

            # Check for meta description
            if 'meta name="description"' not in html and "meta content=" not in html:
                results["issues"].append("Missing meta description")
                results["seo_score"] = max(30, results["seo_score"] - 20)

            # Check for heading structure
            if "<h1" not in html:
                results["issues"].append("Missing H1 heading")
                results["seo_score"] = max(30, results["seo_score"] - 15)

            # Check for image alt text
            img_tags = html.count("<img")
            alt_attributes = html.count("alt=")
            if img_tags > 0 and alt_attributes < img_tags:
                results["issues"].append("Some images missing alt text")
                results["seo_score"] = max(30, results["seo_score"] - 10)

            # Check for robots meta tag that blocks indexing
            if 'meta name="robots" content="noindex' in html:
                results["issues"].append(
                    "Page set to noindex - will not appear in search results"
                )
                results["seo_score"] = max(20, results["seo_score"] - 40)

            # Accessibility checks
            results["accessibility_score"] = 50  # Default

            # Check for alt text on images
            if "<img " in html and (' alt="' not in html or " alt=" not in html):
                results["issues"].append("Images may be missing alt text")
                results["accessibility_score"] = max(
                    30, results["accessibility_score"] - 20
                )

            # Check for form labels
            if "<form" in html and "<label" not in html:
                results["issues"].append("Forms may be missing labels")
                results["accessibility_score"] = max(
                    30, results["accessibility_score"] - 15
                )

            # Best practices checks
            results["best_practices_score"] = 60  # Default

            # Check for basic security headers
            security_headers = [
                "Strict-Transport-Security",
                "Content-Security-Policy",
                "X-Content-Type-Options",
            ]
            missing_headers = [h for h in security_headers if h not in headers]

            if missing_headers:
                results["issues"].append(
                    f"Missing security headers: {', '.join(missing_headers)}"
                )
                results["best_practices_score"] = max(
                    30, results["best_practices_score"] - (len(missing_headers) * 10)
                )

            # Check for JavaScript libraries with known vulnerabilities
            risky_js_libs = ["jquery-1.", "jquery-2.0", "angular.js@1.", "bootstrap-2"]
            for risky_lib in risky_js_libs:
                if risky_lib in html:
                    results["issues"].append(
                        f"Using potentially outdated library: {risky_lib}"
                    )
                    results["best_practices_score"] = max(
                        30, results["best_practices_score"] - 15
                    )
                    break

        except Exception as e:
            results["issues"].append(f"Error during basic analysis: {str(e)}")

    def _calculate_priority(self, results):
        """
        Calculate priority based on analysis results

        Priority levels:
        1 - High priority (No website or critical issues)
        2 - Medium priority (Poor website)
        3 - Low priority (Good website)
        """
        # No website - always highest priority
        if "Error accessing website" in " ".join(results["issues"]):
            return 1

        # Initialize scores with weights for different factors
        weighted_scores = {
            "seo": results["seo_score"] * 0.4,  # SEO has highest weight (40%)
            "performance": results["performance_score"]
            * 0.3,  # Performance is second (30%)
            "accessibility": results["accessibility_score"]
            * 0.15,  # Accessibility (15%)
            "best_practices": results["best_practices_score"]
            * 0.15,  # Best practices (15%)
        }

        # Calculate weighted average score
        weighted_avg = sum(weighted_scores.values())

        # Count critical issues
        critical_seo_issues = any(
            issue in " ".join(results["issues"]).lower()
            for issue in [
                "missing meta description",
                "missing page title",
                "missing h1",
                "noindex",
                "redirect",
            ]
        )

        critical_security_issues = any(
            issue in " ".join(results["issues"]).lower()
            for issue in [
                "not using https",
                "missing security headers",
                "outdated library",
            ]
        )

        # Consider critical issues regardless of scores
        if results["seo_score"] < 40 or critical_seo_issues:
            return 2  # Always medium priority at least for major SEO issues

        # SSL is very important for modern websites
        if not results["has_ssl"]:
            return 2  # Medium priority if no SSL

        # Use the weighted score for the final determination
        if weighted_avg < 55 or len(results["issues"]) > 5 or critical_security_issues:
            return 2  # Medium priority (Poor website)

        # Good website
        return 3  # Low priority (Good website)
