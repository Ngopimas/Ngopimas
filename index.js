// Rebuilds README.md from readme.js: latest posts from the site feed + today's date.
// No dependencies. Needs Node 18+ (built-in fetch).

const fs = require("fs");
const template = require("./readme");

const FEED_URL = "https://romaincoupey.com/rss.xml";
const POST_COUNT = 5;
const README = "./README.md";
const POSTS_BLOCK = /<!-- posts:start -->\n([\s\S]*?)\n<!-- posts:end -->/;

const decode = (s) =>
  s
    .replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g, "$1")
    .replace(/&apos;|&#39;/g, "'")
    .replace(/&quot;/g, '"')
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&amp;/g, "&")
    .trim();

const tag = (xml, name) => {
  const m = xml.match(new RegExp(`<${name}>([\\s\\S]*?)</${name}>`));
  return m ? decode(m[1]) : "";
};

const formatDate = (date) =>
  date.toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
    timeZone: "UTC",
  });

async function fetchPosts() {
  const res = await fetch(FEED_URL);
  if (!res.ok) throw new Error(`feed answered ${res.status}`);
  const xml = await res.text();
  const posts = [...xml.matchAll(/<item>([\s\S]*?)<\/item>/g)]
    .map(([, item]) => ({
      title: tag(item, "title"),
      link: tag(item, "link"),
      date: new Date(tag(item, "pubDate")),
    }))
    .filter((p) => p.title && p.link && !isNaN(p.date))
    .sort((a, b) => b.date - a.date)
    .slice(0, POST_COUNT);
  if (!posts.length) throw new Error("feed has no posts");
  return posts
    .map((p) => `- [${p.title}](${p.link}) · ${formatDate(p.date)}`)
    .join("\n");
}

// If the feed is down, keep the list already in the README rather than blanking it.
function previousPosts() {
  try {
    const m = fs.readFileSync(README, "utf8").match(POSTS_BLOCK);
    return m ? m[1] : "";
  } catch {
    return "";
  }
}

async function main() {
  let posts;
  try {
    posts = await fetchPosts();
  } catch (err) {
    console.warn(`Could not read the feed (${err.message}); keeping the previous list.`);
    posts = previousPosts();
  }
  const readme = template
    .replace("<#posts>", () => posts)
    .replace("<#today_date>", () => formatDate(new Date()));
  fs.writeFileSync(README, readme.trimStart());
}

main();
