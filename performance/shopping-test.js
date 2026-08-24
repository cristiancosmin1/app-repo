import http from "k6/http";
import { check, sleep } from "k6";
import { textSummary } from "https://jslib.k6.io/k6-summary/0.1.0/index.js";

export const options = {
  insecureSkipTLSVerify: true,

  scenarios: {
    shopping: {
      executor: "ramping-vus",
      startVUs: 1,
      stages: [
        { duration: "10s", target: 1 },
      ],
    },
  },

  thresholds: {
    http_req_failed: ["rate<0.01"],
    http_req_duration: ["p(95)<500"],
  },
};

const BASE_URL = __ENV.BASE_URL || "https://app.local";
const KC_URL = __ENV.KC_URL || "https://auth.local";

const CLIENT_ID = __ENV.KC_CLIENT_ID || "shopping-app";
const USERNAME = __ENV.KC_USERNAME || "alice";
const PASSWORD = __ENV.KC_PASSWORD;

function login() {
  if (!PASSWORD) {
    throw new Error(
      "KC_PASSWORD environment variable is required"
    );
  }

  const payload =
    `grant_type=password` +
    `&client_id=${encodeURIComponent(CLIENT_ID)}` +
    `&username=${encodeURIComponent(USERNAME)}` +
    `&password=${encodeURIComponent(PASSWORD)}`;

  const res = http.post(
    `${KC_URL}/realms/devops-lvlup/protocol/openid-connect/token`,
    payload,
    {
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
    }
  );

  console.log(`LOGIN: ${res.status}`);

  check(res, {
    "login status 200": (r) => r.status === 200,
  });

  if (res.status !== 200) {
    console.log(`LOGIN ERROR: ${res.body}`);
    return null;
  }

  return res.json("access_token");
}

export default function () {
  const token = login();

  if (!token) {
    throw new Error("Could not obtain access token");
  }

  const headers = {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
    "X-Run-Id": "perf-test-001",
    "X-Correlation-Id": `corr-${__VU}-${__ITER}-${Date.now()}`,
  };

  // GET /items
  const getRes = http.get(
    `${BASE_URL}/items`,
    {
      headers,
    }
  );

  console.log(`GET: ${getRes.status}`);

  check(getRes, {
    "GET /items = 200": (r) => r.status === 200,
  });

  // POST /items
  const item = {
    name: `k6-item-${__VU}-${__ITER}-${Date.now()}`,
    quantity: 10,
  };

  const postRes = http.post(
    `${BASE_URL}/items`,
    JSON.stringify(item),
    {
      headers,
    }
  );

  console.log(`POST: ${postRes.status}`);

  check(postRes, {
    "POST /items = 201": (r) => r.status === 201,
  });

  if (postRes.status !== 201) {
    console.log(`POST ERROR: ${postRes.body}`);
  }

  sleep(1);
}

export function handleSummary(data) {
  return {
    "performance/results/summary.json": JSON.stringify(
      data,
      null,
      2
    ),
    "performance/results/summary.txt": textSummary(data, {
      indent: " ",
      enableColors: false,
    }),
  };
}
