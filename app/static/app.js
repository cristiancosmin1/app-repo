import Keycloak from "/static/vendor/keycloak.js";

const form = document.getElementById("item-form");
const itemsList = document.getElementById("items-list");
const itemsSection = document.getElementById("items-section");
const message = document.getElementById("message");

const loginButton = document.getElementById("login-button");
const logoutButton = document.getElementById("logout-button");
const userInfo = document.getElementById("user-info");

const keycloak = new Keycloak({
  url: "https://auth.local",
  realm: "devops-lvlup",
  clientId: "shopping-app"
});

function showMessage(text, type = "") {
  message.textContent = text;
  message.className = `message ${type}`;
}

async function ensureFreshToken() {
  try {
    await keycloak.updateToken(30);
  } catch (error) {
    console.error("Token refresh failed:", error);
    await keycloak.login();
    throw error;
  }
}

async function authenticatedFetch(url, options = {}) {
  if (!keycloak.authenticated) {
    throw new Error("Utilizatorul nu este autentificat.");
  }

  await ensureFreshToken();

  const headers = new Headers(options.headers || {});

  headers.set(
    "Authorization",
    `Bearer ${keycloak.token}`
  );

  return fetch(url, {
    ...options,
    headers
  });
}

function updateAuthenticationUI() {
  if (keycloak.authenticated) {
    const username =
      keycloak.tokenParsed?.preferred_username ||
      keycloak.tokenParsed?.email ||
      "utilizator";

    userInfo.textContent = `Autentificat ca: ${username}`;

    loginButton.hidden = true;
    logoutButton.hidden = false;

    form.hidden = false;
    itemsSection.hidden = false;
  } else {
    userInfo.textContent = "Nu ești autentificat.";

    loginButton.hidden = false;
    logoutButton.hidden = true;

    form.hidden = true;
    itemsSection.hidden = true;

    itemsList.innerHTML = "";
  }
}

async function loadItems() {
  if (!keycloak.authenticated) {
    return;
  }

  try {
    const response = await authenticatedFetch("/items");

    if (!response.ok) {
      const errorBody = await response.text();
      throw new Error(`${response.status}: ${errorBody}`);
    }

    const items = await response.json();

    itemsList.innerHTML = "";

    if (items.length === 0) {
      itemsList.innerHTML = "<li>Lista este goală.</li>";
      return;
    }

    for (const item of items) {
      const listItem = document.createElement("li");
      listItem.className = "item";

      const text = document.createElement("span");
      text.textContent =
        `${item.name} — cantitate: ${item.quantity}`;

      const deleteButton = document.createElement("button");
      deleteButton.textContent = "Șterge";
      deleteButton.className = "delete-button";

      deleteButton.addEventListener("click", async () => {
        await deleteItem(item.id);
      });

      listItem.appendChild(text);
      listItem.appendChild(deleteButton);
      itemsList.appendChild(listItem);
    }
  } catch (error) {
    showMessage(
      `Nu am putut încărca produsele: ${error.message}`,
      "error"
    );
  }
}

async function createItem(name, quantity) {
  const response = await authenticatedFetch("/items", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      name,
      quantity
    })
  });

  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(`${response.status}: ${errorBody}`);
  }

  return response.json();
}

async function deleteItem(itemId) {
  try {
    const response = await authenticatedFetch(
      `/items/${itemId}`,
      {
        method: "DELETE"
      }
    );

    if (!response.ok) {
      const errorBody = await response.text();
      throw new Error(`${response.status}: ${errorBody}`);
    }

    showMessage("Produsul a fost șters.", "success");

    await loadItems();
  } catch (error) {
    showMessage(
      `Ștergerea a eșuat: ${error.message}`,
      "error"
    );
  }
}

loginButton.addEventListener("click", async () => {
  await keycloak.login();
});

logoutButton.addEventListener("click", async () => {
  await keycloak.logout({
    redirectUri: window.location.origin
  });
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const nameInput = document.getElementById("name");
  const quantityInput = document.getElementById("quantity");

  const name = nameInput.value.trim();
  const quantity = Number(quantityInput.value);

  if (!name || quantity < 1) {
    showMessage(
      "Completează corect produsul și cantitatea.",
      "error"
    );
    return;
  }

  try {
    await createItem(name, quantity);

    form.reset();
    quantityInput.value = 1;

    showMessage("Produsul a fost adăugat.", "success");

    await loadItems();
  } catch (error) {
    showMessage(
      `Adăugarea a eșuat: ${error.message}`,
      "error"
    );
  }
});

async function initializeAuthentication() {
  try {
    const authenticated = await keycloak.init({
      onLoad: "check-sso",
      pkceMethod: "S256",
      checkLoginIframe: false
    });

    updateAuthenticationUI();

    if (authenticated) {
      await loadItems();
    }
  } catch (error) {
    console.error(
      "Keycloak initialization failed:",
      error
    );

    showMessage(
      "Inițializarea autentificării a eșuat.",
      "error"
    );
  }
}

initializeAuthentication();
