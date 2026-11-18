import { test, expect, type Page } from "@playwright/test";

// Requires the running local demo API/frontend and the explicit seed accounts.
// Synthetic records are retained as demonstration evidence; no user data is deleted.
test("fresh registrations to completed delivery and SMS history", async ({
  browser,
  baseURL,
}) => {
  const suffix = Date.now().toString();
  const password = "DemoPass123!";
  const farmerName = "Demo Farmer " + suffix,
    buyerName = "Demo Buyer " + suffix;
  const farmerEmail = `farmer.${suffix}@example.com`,
    buyerEmail = `buyer.${suffix}@example.com`;
  const produceName = "Demonstration rice " + suffix;
  const admin = await browser.newPage({ baseURL }),
    farmer = await browser.newPage({ baseURL }),
    buyer = await browser.newPage({ baseURL }),
    officer = await browser.newPage({ baseURL }),
    driver = await browser.newPage({ baseURL });
  async function login(page: Page, email: string) {
    await page.goto("/login");
    await page.getByLabel("Email address").fill(email);
    await page.getByLabel("Password").fill(password);
    await page.getByRole("button", { name: "Sign in", exact: true }).click();
    await expect(page).toHaveURL(/\/dashboard$/);
  }
  async function register(
    page: Page,
    role: "farmer" | "buyer",
    name: string,
    email: string,
  ) {
    await page.goto("/register/" + role);
    await page.getByLabel("Full name").fill(name);
    await page.getByLabel("Mobile number").fill("+255712345678");
    if (role === "farmer") {
      await page
        .getByLabel("Farm location / district")
        .fill("Kilosa, Morogoro");
      await page.getByLabel("Farm size (acres)").fill("5");
      await page.getByLabel("Crop categories").fill("Rice");
    } else {
      await page.getByLabel("Business address").fill("Kariakoo, Dar es Salaam");
      await page.getByLabel("Business name").fill("Demo Produce Trading");
    }
    await page.getByLabel("Email address").fill(email);
    await page.getByLabel("Password").fill(password);
    await page.getByRole("button", { name: "Create account" }).click();
    await expect(page).toHaveURL(/\/login\?registered=1$/);
  }
  async function approve(name: string) {
    await admin.goto("/admin");
    const card = admin
      .locator("section.panel")
      .filter({ has: admin.getByRole("heading", { name, exact: true }) });
    await card
      .getByLabel("Verification note")
      .fill("Academic demonstration profile reviewed.");
    await card.getByRole("button", { name: "Save review" }).click();
    await expect(
      admin.getByText("Account updated.", { exact: true }),
    ).toBeVisible();
  }
  await register(farmer, "farmer", farmerName, farmerEmail);
  await login(admin, "admin@tfpmds.demo");
  await approve(farmerName);
  await login(farmer, farmerEmail);
  await farmer.goto("/produce");
  await farmer
    .getByRole("button", { name: "Add produce", exact: true })
    .click();
  await farmer.getByLabel("Produce name").fill(produceName);
  await farmer.getByLabel("Unreserved stock (kg)").fill("600");
  await farmer.getByLabel("Expected price (TZS/kg)").fill("2100");
  await farmer.getByRole("button", { name: "Save listing" }).click();
  await expect(
    farmer.getByText("Produce listing published.", { exact: true }),
  ).toBeVisible();
  await register(buyer, "buyer", buyerName, buyerEmail);
  await approve(buyerName);
  await login(buyer, buyerEmail);
  await buyer.goto("/marketplace");
  await buyer.getByLabel("Search produce").fill(produceName);
  await buyer.getByRole("button", { name: "Apply filters" }).click();
  await buyer.getByRole("link", { name: produceName, exact: true }).click();
  await buyer.getByLabel("Order quantity").fill("50");
  await buyer
    .getByLabel("Delivery address")
    .fill("Kariakoo warehouse, Dar es Salaam");
  await buyer.getByRole("button", { name: "Place order" }).click();
  await expect(buyer).toHaveURL(/\/orders$/);
  const orderTitle = await buyer
    .getByRole("heading", { name: /Order #/ })
    .innerText();
  const orderId = Number(orderTitle.match(/#(\d+)/)![1]);
  await farmer.goto("/orders");
  await farmer
    .getByRole("button", { name: "Accept order", exact: true })
    .click();
  await expect(farmer.getByText("Accepted", { exact: true })).toBeVisible();
  await buyer.reload();
  await buyer
    .getByRole("link", { name: "Simulate payment", exact: true })
    .click();
  await buyer.getByRole("button", { name: "Initiate simulation" }).click();
  await buyer
    .getByRole("button", { name: "Simulate success", exact: true })
    .click();
  await buyer.getByRole("link", { name: "View payment receipt" }).click();
  await expect(buyer.getByText("TZS 105,000", { exact: true })).toBeVisible();
  await login(officer, "logistics@tfpmds.demo");
  await officer.goto("/shipments");
  await officer
    .locator("article.panel")
    .filter({ hasText: `Order #${orderId} ·` })
    .getByRole("link", { name: "Manage & track" })
    .click();
  await officer
    .locator('select[name="transporter_id"]')
    .selectOption({ label: "Safari Fresh Transport · Morogoro" });
  await officer.getByRole("button", { name: "Assign transporter" }).click();
  await expect(
    officer.getByText("Transporter assigned and notified.", { exact: true }),
  ).toBeVisible();
  const trackingUrl = officer.url();
  await login(driver, "transporter@tfpmds.demo");
  await driver.goto(trackingUrl);
  for (const [state, label] of [
    ["ready_for_pickup", "Ready For Pickup"],
    ["picked_up", "Picked Up"],
    ["in_transit", "In Transit"],
    ["delivered", "Delivered"],
  ]) {
    await driver.getByLabel("Next status").selectOption(state);
    await driver.getByLabel("Current location").fill("Dar es Salaam");
    await driver
      .getByLabel("Tracking note")
      .fill("Automated academic demonstration milestone.");
    await driver.getByRole("button", { name: "Save milestone" }).click();
    await expect(driver.locator(".timeline-event").first()).toContainText(
      label,
    );
  }
  for (const page of [farmer, buyer]) {
    await page.goto(trackingUrl);
    await expect(
      page.getByRole("heading", { name: "The journey" }),
    ).toBeVisible();
    await expect(page.locator(".timeline-event")).toHaveCount(6);
  }
  await buyer.goto("/orders");
  await buyer
    .getByRole("button", { name: "Confirm receipt & complete" })
    .click();
  await expect(buyer.getByText("Completed", { exact: true })).toBeVisible();
  await admin.goto("/reports");
  await expect(
    admin.getByRole("heading", { name: "Reports & analytics" }),
  ).toBeVisible();
  await admin.goto("/admin/sms");
  await expect(admin.locator("tbody")).toContainText(farmerName);
  await expect(admin.locator("tbody")).toContainText(buyerName);
});
