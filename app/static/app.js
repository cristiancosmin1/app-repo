const form = document.getElementById("item-form");
const itemsList = document.getElementById("items-list");
const message = document.getElementById("message");

function showMessage(text, type = "") {
  message.textContent = text;
  message.className = `message ${type}`;
}

async function loadItems() {
  try {
    const response = await fetch("/items");

    if (!response.ok) {
      throw new Error(`Eroare HTTP: ${response.status}`);
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
      text.textContent = `${item.name} — cantitate: ${item.quantity}`;

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
    showMessage(`Nu am putut încărca produsele: ${error.message}`, "error");
  }
}

async function createItem(name, quantity) {
  const response = await fetch("/items", {
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
    const response = await fetch(`/items/${itemId}`, {
      method: "DELETE"
    });

    if (!response.ok) {
      throw new Error(`Eroare HTTP: ${response.status}`);
    }

    showMessage("Produsul a fost șters.", "success");
    await loadItems();
  } catch (error) {
    showMessage(`Ștergerea a eșuat: ${error.message}`, "error");
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const nameInput = document.getElementById("name");
  const quantityInput = document.getElementById("quantity");

  const name = nameInput.value.trim();
  const quantity = Number(quantityInput.value);

  if (!name || quantity < 1) {
    showMessage("Completează corect produsul și cantitatea.", "error");
    return;
  }

  try {
    await createItem(name, quantity);

    form.reset();
    quantityInput.value = 1;

    showMessage("Produsul a fost adăugat.", "success");

    await loadItems();
  } catch (error) {
    showMessage(`Adăugarea a eșuat: ${error.message}`, "error");
  }
});

loadItems();
