/**
 * Reuni Landing Page (landing.js)
 * Premium interactive features, spring metrics count-up, geolocation selector,
 * magnetic buttons, and CSP compliance (no inline scripts).
 */

document.addEventListener("DOMContentLoaded", () => {
  // Check user preference for reduced motion
  const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ==========================================================================
     1. BENTO CARD MOUSE PROXIMITY GLOW EFFECT
     ========================================================================== */
  const bentoCards = document.querySelectorAll(".bento-card");
  bentoCards.forEach(card => {
    card.addEventListener("mousemove", e => {
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      card.style.setProperty("--mouse-x", `${x}px`);
      card.style.setProperty("--mouse-y", `${y}px`);
    });
  });

  /* ==========================================================================
     2. DYNAMIC EXPERIENCE SHOWCASE WIDGET
     ========================================================================== */
  const studentBtn = document.getElementById("segment-student");
  const partnerBtn = document.getElementById("segment-partner");
  const studentScreen = document.getElementById("showcase-student");
  const partnerScreen = document.getElementById("showcase-partner");

  let simulationInterval = null;

  function switchShowcaseMode(mode) {
    if (mode === "student") {
      studentBtn.classList.add("segment-btn--active");
      partnerBtn.classList.remove("segment-btn--active");
      studentScreen.classList.add("showcase-screen--active");
      partnerScreen.classList.remove("showcase-screen--active");
      startStudentSimulation();
    } else {
      partnerBtn.classList.add("segment-btn--active");
      studentBtn.classList.remove("segment-btn--active");
      partnerScreen.classList.add("showcase-screen--active");
      studentScreen.classList.remove("showcase-screen--active");
      stopStudentSimulation();
      animatePartnerCharts();
    }
  }

  if (studentBtn && partnerBtn) {
    studentBtn.addEventListener("click", () => switchShowcaseMode("student"));
    partnerBtn.addEventListener("click", () => switchShowcaseMode("partner"));
  }

  // A. Student Mode: Auto-Interactive Claim & Handshake Simulation
  const mockCards = document.querySelectorAll(".mock-card");
  const handshakeOverlay = document.getElementById("handshake-overlay");
  const simPinDigits = document.querySelectorAll(".sim-digit");
  
  function startStudentSimulation() {
    stopStudentSimulation();
    
    // Periodically simulate claiming an item (every 8 seconds)
    simulationInterval = setInterval(() => {
      // Pick the second card (Bicycle) for the demo
      const targetCard = mockCards[1];
      if (!targetCard) return;

      // Phase 1: Highlights card
      targetCard.style.borderColor = "var(--landing-teal)";
      targetCard.style.transform = "scale(1.02)";
      
      setTimeout(() => {
        // Phase 2: Show WhatsApp / PIN handshake overlay
        if (handshakeOverlay) {
          handshakeOverlay.classList.add("handshake-simulation--visible");
          
          // Animate PIN digits typing (e.g. 5, 8, 2, 4)
          const pinDigits = ["5", "8", "2", "4"];
          simPinDigits.forEach(d => { d.textContent = ""; d.style.borderColor = "rgba(255,255,255,0.1)"; });
          
          pinDigits.forEach((digit, idx) => {
            setTimeout(() => {
              if (simPinDigits[idx]) {
                simPinDigits[idx].textContent = digit;
                simPinDigits[idx].style.borderColor = "var(--landing-teal)";
              }
            }, (idx + 1) * 450);
          });
        }
      }, 1200);

      setTimeout(() => {
        // Phase 3: Successful transaction
        if (handshakeOverlay) {
          handshakeOverlay.classList.remove("handshake-simulation--visible");
        }
        targetCard.style.borderColor = "rgba(255,255,255,0.03)";
        targetCard.style.transform = "none";
        
        // Show status badge as Sold
        const badge = targetCard.querySelector(".mock-badge");
        if (badge) {
          badge.textContent = "Sold / Saved";
          badge.style.background = "rgba(45, 212, 191, 0.15)";
          badge.style.color = "var(--landing-teal)";
        }
      }, 5000);

      // Reset badge after simulation loop completes
      setTimeout(() => {
        const badge = targetCard.querySelector(".mock-badge");
        if (badge) {
          badge.textContent = "12 kg saved";
          badge.style.background = "rgba(52, 211, 153, 0.1)";
          badge.style.color = "var(--landing-emerald)";
        }
      }, 7800);

    }, 8000);
  }

  function stopStudentSimulation() {
    if (simulationInterval) {
      clearInterval(simulationInterval);
      simulationInterval = null;
    }
    if (handshakeOverlay) {
      handshakeOverlay.classList.remove("handshake-simulation--visible");
    }
    mockCards.forEach(c => {
      c.style.borderColor = "rgba(255,255,255,0.03)";
      c.style.transform = "none";
    });
  }

  // B. Partner Mode: Simulated ESG Charts
  const chartFills = document.querySelectorAll(".mock-bar-fill");
  function animatePartnerCharts() {
    chartFills.forEach(fill => {
      const targetWidth = fill.getAttribute("data-width") || "0%";
      fill.style.width = "0%";
      setTimeout(() => {
        fill.style.width = targetWidth;
      }, 150);
    });
  }

  // Initialize student simulation on start
  startStudentSimulation();

  /* ==========================================================================
     3. SPRING METRIC COUNT-UP ANIMATION
     ========================================================================== */
  const statsSection = document.getElementById("bento-card-impact");
  const statsElements = document.querySelectorAll(".impact-stat-number");

  function animateCountUp(element, targetValue) {
    if (prefersReducedMotion) {
      element.textContent = targetValue.toFixed(element.dataset.decimals === "0" ? 0 : 1);
      return;
    }

    let startTimestamp = null;
    const duration = 1500; // ms
    const isInt = element.dataset.decimals === "0";

    function step(timestamp) {
      if (!startTimestamp) startTimestamp = timestamp;
      const progress = Math.min((timestamp - startTimestamp) / duration, 1);
      
      // Snappy cubic ease-out
      const easeProgress = 1 - Math.pow(1 - progress, 3);
      const currentValue = easeProgress * targetValue;
      
      element.textContent = isInt ? Math.floor(currentValue) : currentValue.toFixed(1);
      
      if (progress < 1) {
        window.requestAnimationFrame(step);
      } else {
        element.textContent = isInt ? Math.floor(targetValue) : targetValue.toFixed(1);
      }
    }
    window.requestAnimationFrame(step);
  }

  if (statsSection && statsElements.length > 0) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          statsElements.forEach(el => {
            const target = parseFloat(el.getAttribute("data-target") || "0");
            animateCountUp(el, target);
          });
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1 });
    
    observer.observe(statsSection);
  }

  /* ==========================================================================
     4. GEOLOCATION SEARCH SELECTOR & NEAREST CAMPUS
     ========================================================================== */
  const searchInput = document.getElementById("campus-search-input");
  const uniButtons = document.querySelectorAll(".uni-entry-btn");
  const detectLocationBtn = document.getElementById("detect-location-btn");

  // Search Filter
  if (searchInput) {
    searchInput.addEventListener("input", (e) => {
      const term = e.target.value.toLowerCase().trim();
      uniButtons.forEach(btn => {
        const uniName = btn.querySelector(".uni-entry-btn__name").textContent.toLowerCase();
        const uniDomain = btn.getAttribute("data-domain").toLowerCase();
        if (uniName.includes(term) || uniDomain.includes(term)) {
          btn.style.display = "flex";
        } else {
          btn.style.display = "none";
        }
      });
    });
  }

  // Geolocation Distance Calculations
  const CAMPUSES = [
    { id: "brookes", name: "Oxford Brookes University", lat: 51.7538, lon: -1.2238 },
    { id: "oxford", name: "University of Oxford", lat: 51.7520, lon: -1.2577 }
  ];

  function calculateDistance(lat1, lon1, lat2, lon2) {
    // Haversine formula
    const R = 6371; // km
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = 
      Math.sin(dLat/2) * Math.sin(dLat/2) +
      Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * 
      Math.sin(dLon/2) * Math.sin(dLon/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c;
  }

  function highlightClosestCampus(userLat, userLon) {
    let minDistance = Infinity;
    let closestCampusId = null;

    CAMPUSES.forEach(campus => {
      const dist = calculateDistance(userLat, userLon, campus.lat, campus.lon);
      if (dist < minDistance) {
        minDistance = dist;
        closestCampusId = campus.id;
      }
    });

    if (closestCampusId) {
      uniButtons.forEach(btn => {
        const btnId = btn.getAttribute("data-id");
        if (btnId === closestCampusId) {
          btn.classList.add("uni-entry-btn--highlighted");
          const distLabel = btn.querySelector(".uni-entry-btn__listings");
          if (distLabel) {
            const listingsText = distLabel.dataset.listingsCount || "0";
            distLabel.textContent = `${listingsText} active listings · Nearest to you (${minDistance.toFixed(1)} km away)`;
          }
        } else {
          btn.classList.remove("uni-entry-btn--highlighted");
          const distLabel = btn.querySelector(".uni-entry-btn__listings");
          if (distLabel) {
            distLabel.textContent = `${distLabel.dataset.listingsCount || "0"} active listings`;
          }
        }
      });
    }
  }

  if (detectLocationBtn) {
    detectLocationBtn.addEventListener("click", () => {
      if (navigator.geolocation) {
        detectLocationBtn.textContent = "Locating...";
        navigator.geolocation.getCurrentPosition(
          (position) => {
            highlightClosestCampus(position.coords.latitude, position.coords.longitude);
            detectLocationBtn.textContent = "Location Detected";
            detectLocationBtn.style.color = "var(--landing-teal)";
          },
          (err) => {
            console.warn("Geolocation permission denied or error:", err);
            detectLocationBtn.textContent = "Location access denied";
            detectLocationBtn.style.color = "var(--landing-orange)";
          }
        );
      } else {
        // Fallback for non-secure contexts (e.g. reuni.local) in development testing
        detectLocationBtn.textContent = "Locating (Mock)...";
        setTimeout(() => {
          // Mock Brookes coordinate (51.7538, -1.2238)
          highlightClosestCampus(51.7530, -1.2250);
          detectLocationBtn.textContent = "Brookes Detected (Mock)";
          detectLocationBtn.style.color = "var(--landing-teal)";
        }, 850);
      }
    });
  }

  /* ==========================================================================
     5. RIVALRY SEASON CUP PROGRESS ANIMATION
     ========================================================================== */
  const rivalrySection = document.getElementById("bento-card-rivalry");
  const rivalryFills = document.querySelectorAll(".rivalry-progress-fill");

  if (rivalrySection && rivalryFills.length > 0) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          rivalryFills.forEach(fill => {
            const targetPct = fill.getAttribute("data-pct") || "50%";
            fill.style.width = targetPct;
          });
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1 });
    
    observer.observe(rivalrySection);
  }

  /* ==========================================================================
     6. COOKIE SETTING ON CAMPUS NODE SELECTION
     ========================================================================== */
  uniButtons.forEach(btn => {
    btn.addEventListener("click", (e) => {
      const slug = btn.getAttribute("data-id"); // e.g. "brookes"
      if (slug) {
        // Dynamically compute parent domain for local development or production
        const hostParts = window.location.hostname.split('.');
        let domainAttr = "";
        if (hostParts.length >= 2) {
          const baseParts = hostParts.slice(-2);
          domainAttr = `; domain=.${baseParts.join('.')}`;
        }
        // Set selected_uni cookie for 1 year, SameSite=Lax
        document.cookie = `selected_uni=${slug}; path=/; max-age=31536000; SameSite=Lax${domainAttr};`;
      }
    });
  });

  /* ==========================================================================
     7. MAGNETIC HOVER BUTTONS
     ========================================================================== */
  const magneticButtons = document.querySelectorAll(".btn--magnetic");
  
  if (!prefersReducedMotion) {
    magneticButtons.forEach(btn => {
      btn.addEventListener("mousemove", (e) => {
        const rect = btn.getBoundingClientRect();
        const x = e.clientX - rect.left - rect.width / 2;
        const y = e.clientY - rect.top - rect.height / 2;
        
        // Translate button slightly in pointer direction
        btn.style.transform = `translate(${x * 0.35}px, ${y * 0.35}px)`;
        const icon = btn.querySelector(".btn__icon-wrapper");
        if (icon) {
          icon.style.transform = `translate(${x * 0.15}px, ${y * 0.15}px)`;
        }
      });
      
      btn.addEventListener("mouseleave", () => {
        btn.style.transform = "translate(0px, 0px)";
        const icon = btn.querySelector(".btn__icon-wrapper");
        if (icon) {
          icon.style.transform = "translate(0px, 0px)";
        }
      });
    });
  }

});
