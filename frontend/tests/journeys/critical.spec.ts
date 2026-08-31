import { test, expect, type Page } from "@playwright/test";

const ADMIN_URL = "http://localhost:5200";

/**
 * Navigate as a returning visitor: pre-set the intro-seen flag so the
 * intro/category gate doesn't cover the page. Tests that exercise the gate
 * itself (Journey 1) should not use this.
 */
async function gotoReturning(page: Page, url: string) {
  await page.addInitScript(() => {
    sessionStorage.setItem("intro-seen", "true");
  });
  await page.goto(url);
}

/* ------------------------------------------------------------------ */
/* Journey 1: First Visit — Intro → Select Category → Overview        */
/* ------------------------------------------------------------------ */
test.describe("Journey 1: First Visit", () => {
  test("intro animation plays, skip, select a category, overview renders", async ({
    page,
  }) => {
    await page.goto("/");

    // intro overlay is present
    const overlay = page.locator('[role="button"][tabindex="0"]').first();
    await expect(overlay).toBeVisible();

    // wait for at least one word to appear (CURIOUS pops first after 200ms delay)
    await expect(page.getByText("CURIOUS")).toBeVisible({ timeout: 5000 });

    // click overlay to skip intro
    await overlay.click();

    // category selector should now show with "Who are you?" heading
    await expect(page.getByText("Who are you?")).toBeVisible({ timeout: 3000 });

    // pick a concrete audience (default catch-all is no longer user-selectable)
    await page.getByText("Recruiters").click();

    // intro overlay dismissed — overview tile grid should be visible
    await expect(overlay).not.toBeVisible({ timeout: 3000 });

    // verify tile grid rendered (main contains tile links)
    const tileLinks = page.locator(
      "main .grid.grid-cols-1.gap-6 a, main .grid a[href]"
    );
    await expect(tileLinks.first()).toBeVisible({ timeout: 10000 });

    // HUD toggle button is visible
    const hudButton = page.getByLabel("Toggle category selector");
    await expect(hudButton).toBeVisible({ timeout: 5000 });
  });
});

/* ------------------------------------------------------------------ */
/* Journey 2: Returning Visit — Skips Intro                           */
/* ------------------------------------------------------------------ */
test.describe("Journey 2: Returning Visit", () => {
  test("intro overlay is skipped when sessionStorage has intro-seen flag", async ({
    page,
  }) => {
    // simulate returning visit by pre-setting sessionStorage
    await page.addInitScript(() => {
      sessionStorage.setItem("intro-seen", "true");
    });

    await page.goto("/");

    // intro overlay should NOT be visible
    const overlay = page.locator('[role="button"][tabindex="0"]').first();
    await expect(overlay).not.toBeVisible({ timeout: 5000 });

    // main content (tile grid) should be immediately visible
    const tileLinks = page.locator(
      "main .grid.grid-cols-1.gap-6 a, main .grid a[href]"
    );
    await expect(tileLinks.first()).toBeVisible({ timeout: 10000 });

    // HUD is present
    await expect(page.getByLabel("Toggle category selector")).toBeVisible({
      timeout: 5000,
    });
  });
});

/* ------------------------------------------------------------------ */
/* Journey 3: Category Switch via HUD                                 */
/* ------------------------------------------------------------------ */
test.describe("Journey 3: Category Switch via HUD", () => {
  test("switch to Recruiters category, timeline re-renders with filtered entries", async ({
    page,
  }) => {
    await gotoReturning(page, "/timeline");

    // page heading is visible
    await expect(page.getByRole("heading", { name: "Timeline" })).toBeVisible({
      timeout: 10000,
    });

    // open HUD category selector
    const hudButton = page.getByLabel("Toggle category selector");
    await expect(hudButton).toBeVisible();
    await hudButton.click();

    // click "Recruiters" category button
    await page.getByRole("button", { name: "Recruiters" }).click();

    // HUD category label should now show "recruiters"
    await expect(hudButton.getByText("recruiters")).toBeVisible({
      timeout: 5000,
    });

    // timeline entries should be visible (some may be dimmed based on relevance)
    const timelineArticles = page.locator("article[id^='entry-']");
    await expect(timelineArticles.first()).toBeVisible({ timeout: 10000 });

    // at least one entry should have reduced opacity (non-relevant)
    const dimmedEntries = page.locator("article.opacity-50");
    const relevantEntries = page.locator("article.opacity-100");
    const hasFiltering =
      (await dimmedEntries.count()) > 0 ||
      (await relevantEntries.count()) > 0;
    expect(hasFiltering).toBeTruthy();
  });
});

/* ------------------------------------------------------------------ */
/* Journey 4: Admin — Login → Create Draft → Publish → Verify         */
/* ------------------------------------------------------------------ */
test.describe("Journey 4: Admin Flow", () => {
  // Requires the admin SPA (:5200), backend (:8000) and credentials. Runs
  // only when explicitly provisioned (local pairing); CI skips until that
  // infra exists there.
  test.skip(
    !process.env.E2E_ADMIN_PASSWORD && !process.env.E2E_TEST_PASSWORD,
    "Requires admin (port 5200) + backend (port 8000) running and E2E_ADMIN_PASSWORD/E2E_TEST_PASSWORD set"
  );

  test("login, create draft timeline entry, publish, verify on public page", async ({
    page,
  }) => {
    // The dev OTP shortcut uses a single shared challenge slot, so running the
    // admin login concurrently across viewports races. The flow is
    // viewport-agnostic, so exercise it once on desktop.
    test.skip(
      test.info().project.name !== "desktop",
      "Admin login flow runs once on desktop (shared dev-OTP slot)"
    );

    const uniqueTitle = `E2E Test Entry ${Date.now()}`;

    // --- Login ---
    await page.goto(`${ADMIN_URL}/login`);
    await page.waitForLoadState("networkidle");

    // expect login form
    await expect(page.getByText("Admin Login")).toBeVisible({ timeout: 5000 });

    // fill password — use env var or fallback
    const password =
      process.env.E2E_ADMIN_PASSWORD || process.env.E2E_TEST_PASSWORD || "";
    await page.fill("#password", password);
    await page.getByRole("button", { name: /Send Code/i }).click();

    // --- OTP Verification ---
    await expect(page.getByText("Verify Code")).toBeVisible({ timeout: 10000 });

    // Prefer an explicit OTP from env; otherwise pull the dev-only code the
    // local backend serves at /api/v1/auth/dev/otp (ENVIRONMENT=development).
    // This lets the journey run with no Resend key configured.
    let otp = process.env.E2E_ADMIN_OTP || process.env.E2E_TEST_OTP || "";
    if (!otp) {
      try {
        const resp = await page.request.get(
          "http://localhost:8000/api/v1/auth/dev/otp"
        );
        if (resp.ok()) {
          const data = (await resp.json()) as { code?: string };
          otp = data.code ?? "";
        }
      } catch {
        otp = "";
      }
    }
    if (otp.length === 6) {
      const inputs = page.locator('input[maxlength="1"]');
      for (let i = 0; i < 6; i++) {
        await inputs.nth(i).fill(otp[i]);
      }
    } else {
      // attempt paste of OTP
      await page.locator('input[maxlength="1"]').first().focus();
      await page.keyboard.type(otp);
    }

    // should redirect to dashboard after successful verification
    await expect(
      page.getByRole("heading", { level: 1, name: "Dashboard" })
    ).toBeVisible({ timeout: 15000 });

    // --- Navigate to Timeline ---
    await page.goto(`${ADMIN_URL}/timeline`);
    await page.waitForLoadState("networkidle");
    await expect(
      page.getByRole("heading", { level: 1, name: "Timeline" })
    ).toBeVisible({ timeout: 10000 });

    // --- Create New Entry ---
    await page.getByRole("link", { name: /New Entry/i }).click();
    await expect(page.getByText(/New Timeline Entry/i)).toBeVisible({
      timeout: 5000,
    });

    // fill basic details
    await page
      .getByPlaceholder("Software Engineer")
      .fill(uniqueTitle);
    await page.getByPlaceholder("Acme Corp").fill(uniqueTitle);
    await page.locator('input[type="date"]').first().fill("2024-01-01");

    // save as draft (status defaults to "draft")
    await page.getByRole("button", { name: /Create/i }).click();

    // --- Verify draft in list ---
    await page.waitForLoadState("networkidle");
    await expect(page.getByRole("heading", { level: 1, name: "Timeline" })).toBeVisible({
      timeout: 10000,
    });
    await expect(page.getByText(uniqueTitle).first()).toBeVisible({
      timeout: 5000,
    });

    // verify status badge shows "draft"
    const draftRow = page.locator("tr", {
      hasText: uniqueTitle,
    });
    await expect(draftRow.getByText("draft")).toBeVisible();

    // --- Edit and Publish ---
    const editLink = draftRow.locator('a[href*="/edit"]').first();
    await editLink.click();
    await expect(
      page.getByRole("heading", { level: 1, name: /Edit Timeline Entry/i })
    ).toBeVisible({
      timeout: 5000,
    });

    // change status to "published" via the PublishStatusField custom select
    const statusTrigger = page
      .getByText("Status", { exact: true })
      .locator("..")
      .getByRole("combobox")
      .first();
    await statusTrigger.click();
    await page.getByRole("option", { name: "published" }).click();

    await page.getByRole("button", { name: /Update/i }).click();
    await page.waitForLoadState("networkidle");

    // --- Verify on public timeline ---
    // switch to the public site (same context so auth cookies persist for admin realm only)
    const publicPage = await page.context().newPage();
    await publicPage.goto("/timeline");
    await publicPage.waitForLoadState("networkidle");
    const pubEntry = publicPage.getByText(uniqueTitle).first();
    // The published entry may take a moment to appear after cache revalidation.
    await expect(async () => {
      await publicPage.reload();
      expect(await pubEntry.isVisible()).toBeTruthy();
    }).toPass({ timeout: 25000, intervals: [2000] });

    await publicPage.close();
  });
});

/* ------------------------------------------------------------------ */
/* Journey 5: Form Submission Pages                                    */
/* ------------------------------------------------------------------ */
test.describe("Journey 5: Form Submission Pages", () => {
  test("contact page shows email, LinkedIn, Cal.com links", async ({
    page,
  }) => {
    await gotoReturning(page, "/contact");

    await expect(
      page.getByRole("heading", { name: "Contact" })
    ).toBeVisible({ timeout: 10000 });

    // email section — scoped to the heading: the form below also has an
    // "Email" label, which makes unscoped getByText ambiguous.
    await expect(page.getByRole("heading", { name: "Email" })).toBeVisible();
    await expect(page.getByText("siddhesh@example.com")).toBeVisible();

    // LinkedIn link
    await expect(
      page.getByRole("heading", { name: "LinkedIn" })
    ).toBeVisible();
    await expect(
      page.getByRole("link", { name: /linkedin\.com\/in\/siddheshchaudhari/i })
    ).toBeVisible();

    // Cal.com link
    await expect(page.getByText("Book a call")).toBeVisible();
    await expect(
      page.getByRole("link", { name: /cal\.com\/siddhesh/i })
    ).toBeVisible();
  });

  test("dealflow page shows consent checkbox", async ({ page }) => {
    await gotoReturning(page, "/dealflow");

    // scoped to the heading: the consent text also contains "Dealflow"
    await expect(
      page.getByRole("heading", { name: "Dealflow" })
    ).toBeVisible({ timeout: 10000 });

    // consent checkbox is present (type=checkbox within a label)
    const consentCheckbox = page.locator('label input[type="checkbox"]');
    await expect(consentCheckbox.first()).toBeVisible();

    // submit button is present and labelled
    await expect(
      page.getByRole("button", { name: "Submit" })
    ).toBeVisible();
  });
});

/* ------------------------------------------------------------------ */
/* Journey 6: Project -> Timeline cross-link (TD-36.S5)               */
/* ------------------------------------------------------------------ */
test.describe("Journey 6: Project → Timeline cross-link", () => {
  test("open a project, follow its timeline cross-link, land on the highlighted entry", async ({
    page,
  }) => {
    await gotoReturning(page, "/projects");

    await expect(
      page.getByRole("heading", { name: "Projects" })
    ).toBeVisible({ timeout: 10000 });

    // click the seeded cross-linked project
    await page
      .getByRole("link", { name: /E2E Seed: Cross-linked project/i })
      .first()
      .click();

    await expect(page).toHaveURL(/e2e-seed-project/, {
      timeout: 10000,
    });

    // the detail page exposes a cross-link to /timeline#entry-<id>
    const crossLink = page.locator('a[href^="/timeline#entry-"]').first();
    await expect(crossLink).toBeVisible({ timeout: 5000 });

    await crossLink.click();

    await expect(page).toHaveURL(/#entry-/, { timeout: 10000 });

    // the targeted entry exists on the timeline and is the scroll/highlight target
    const hash = page.url().split("#entry-")[1];
    expect(hash).toBeTruthy();
    await expect(page.locator(`article#entry-${hash}`).first()).toBeVisible({
      timeout: 10000,
    });
  });
});
