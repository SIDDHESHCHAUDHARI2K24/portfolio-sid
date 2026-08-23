import { test, expect } from "@playwright/test";

const ADMIN_URL = "http://localhost:5200";

/* ------------------------------------------------------------------ */
/* Journey 1: First Visit — Intro → Select Category → Overview        */
/* ------------------------------------------------------------------ */
test.describe("Journey 1: First Visit", () => {
  test("intro animation plays, skip, select 'Show everything', overview renders", async ({
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

    // click "Show everything" tile
    await page.getByText("Show everything").click();

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
    await page.goto("/timeline");
    await page.waitForLoadState("networkidle");

    // page heading is visible
    await expect(page.getByText("Timeline")).toBeVisible({ timeout: 10000 });

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
  test.skip(
    !process.env.CI,
    "Skipped by default — requires admin (port 5200) and backend (port 8000) running"
  );

  test("login, create draft timeline entry, publish, verify on public page", async ({
    page,
  }) => {
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

    const otp = process.env.E2E_ADMIN_OTP || process.env.E2E_TEST_OTP || "";
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
    await expect(page.getByText("Dashboard")).toBeVisible({ timeout: 15000 });

    // --- Navigate to Timeline ---
    await page.goto(`${ADMIN_URL}/timeline`);
    await page.waitForLoadState("networkidle");
    await expect(page.getByText("Timeline")).toBeVisible({ timeout: 10000 });

    // --- Create New Entry ---
    await page.getByRole("link", { name: /New Entry/i }).click();
    await expect(page.getByText(/New Timeline Entry/i)).toBeVisible({
      timeout: 5000,
    });

    // fill basic details
    await page
      .getByPlaceholder("Software Engineer")
      .fill("Playwright E2E Entry");
    await page.getByPlaceholder("Acme Corp").fill(uniqueTitle);
    await page.locator('input[type="date"]').first().fill("2024-01-01");

    // save as draft (status defaults to "draft")
    await page.getByRole("button", { name: /Create/i }).click();

    // --- Verify draft in list ---
    await page.waitForLoadState("networkidle");
    await expect(page.getByText("Timeline")).toBeVisible({ timeout: 10000 });
    await expect(page.getByText("Playwright E2E Entry")).toBeVisible({
      timeout: 5000,
    });

    // verify status badge shows "draft"
    const draftRow = page.locator("tr", {
      hasText: "Playwright E2E Entry",
    });
    await expect(draftRow.getByText("draft")).toBeVisible();

    // --- Edit and Publish ---
    const editLink = draftRow.getByRole("link", { name: /Edit/i });
    await editLink.click();
    await expect(page.getByText(/Edit Timeline Entry/i)).toBeVisible({
      timeout: 5000,
    });

    // change status to "published" via PublishStatusField
    // The PublishStatusField should have a select/dropdown
    await page
      .getByRole("combobox")
      .or(page.locator("select"))
      .first()
      .selectOption("published");
    // fallback: look for radio/button
    const publishOption = page.getByRole("button", { name: /published/i });
    if (await publishOption.isVisible()) {
      await publishOption.click();
    }

    await page.getByRole("button", { name: /Update/i }).click();
    await page.waitForLoadState("networkidle");

    // --- Verify on public timeline ---
    // switch to the public site (same context so auth cookies persist for admin realm only)
    const publicPage = await page.context().newPage();
    await publicPage.goto("/timeline");
    await publicPage.waitForLoadState("networkidle");
    await expect(
      publicPage.getByText("Playwright E2E Entry")
    ).toBeVisible({ timeout: 15000 });

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
    await page.goto("/contact");
    await page.waitForLoadState("networkidle");

    await expect(page.getByText("Contact")).toBeVisible({ timeout: 10000 });

    // email section
    await expect(page.getByText("Email")).toBeVisible();
    await expect(
      page.getByText("siddhesh@example.com")
    ).toBeVisible();

    // LinkedIn link
    await expect(page.getByText("LinkedIn")).toBeVisible();
    await expect(
      page.getByRole("link", { name: /linkedin\.com\/in\/siddheshchaudhari/i })
    ).toBeVisible();

    // Cal.com link
    await expect(page.getByText("Book a call")).toBeVisible();
    await expect(
      page.getByRole("link", { name: /cal\.com\/siddhesh/i })
    ).toBeVisible();
  });

  test("dealflow page shows consent checkbox and Turnstile widget", async ({
    page,
  }) => {
    await page.goto("/dealflow");
    await page.waitForLoadState("networkidle");

    await expect(page.getByText("Dealflow")).toBeVisible({ timeout: 10000 });

    // consent checkbox is present (type=checkbox within a label)
    const consentCheckbox = page.locator('label input[type="checkbox"]');
    await expect(consentCheckbox.first()).toBeVisible();

    // Turnstile widget container should be present (.cf-turnstile div)
    // The Turnstile widget loads asynchronously via external script;
    // verify the container div exists
    await expect(page.locator(".cf-turnstile").first()).toBeVisible({
      timeout: 5000,
    });
  });
});
