// Script adapted from https://github.com/Melvynx/

const { promises: fs } = require("fs");
const readme = require("./readme");

const msInOneDay = 1000 * 60 * 60 * 24;

const today = new Date();

function generateNewREADME() {
  const readmeRow = readme.split("\n");

  function updateIdentifier(identifier, replaceText) {
    const identifierIndex = findIdentifierIndex(readmeRow, identifier);
    if (!readmeRow[identifierIndex]) return;
    readmeRow[identifierIndex] = readmeRow[identifierIndex].replace(
      `<#${identifier}>`,
      replaceText
    );
  }

  const identifierToUpdate = {
    day_before_new_years: getDBNWSentence(),
    emoji: getEmoji(),
    today_date: getTodayDate(),
    bot_signing: getBotSigning(),
  };

  Object.entries(identifierToUpdate).forEach(([key, value]) => {
    updateIdentifier(key, value);
  });

  return readmeRow.join("\n");
}

const moodByDay = {
  1: "humor",
  2: "passion",
  3: "pleasure",
  4: "happiness",
  5: "humanity",
  6: "friendliness",
  7: "love",
};

function getBotSigning() {
  const mood = moodByDay[today.getDay()];
  return `🤖 This README.md is updated with ${mood}, by a bot ❤️`;
}

function getTodayDate() {
  return today.toDateString();
}

function getEmoji() {
  // test if we are in a PAIR DAY
  return today.getDate() % 2 === 0
    ? Math.floor(Math.random() * 2)
      ? " ✨"
      : "."
    : " 🎉";
}

function getDBNWSentence() {
  const nextYear = today.getFullYear() + 1;
  const nextYearDate = new Date(String(nextYear));

  const timeUntilNewYear = nextYearDate - today;
  const dayUntilNewYear = Math.round(timeUntilNewYear / msInOneDay);

  return `**${dayUntilNewYear} day before ${nextYear} ⏱**`;
}

const findIdentifierIndex = (rows, identifier) =>
  rows.findIndex((r) => Boolean(r.match(new RegExp(`<#${identifier}>`, "i"))));

const updateREADMEFile = (text) =>
  fs.writeFile("./README.md", text, () => console.log(text));

function main() {
  const newREADME = generateNewREADME();
  console.log(newREADME);
  updateREADMEFile(newREADME);
}

main();
