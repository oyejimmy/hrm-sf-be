const crypto = require('crypto');
const bcrypt = require('bcrypt');

/**
 * Generate a secure temporary password and its bcrypt hash.
 * @param options length (default 10), includeSymbols (default false), hashRounds (default 10)
 * @returns { tempPassword, hashedPassword }
 */
async function generateTempPassword(options = {}) {
  const { length = 10, includeSymbols = false, hashRounds = 10 } = options;

  const alpha = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
  const symbols = "!@#$%&*?"; // safe subset
  const charset = includeSymbols ? alpha + symbols : alpha;

  // Generate secure random bytes and map to characters in charset
  const bytes = crypto.randomBytes(length);
  let tempPassword = "";
  for (let i = 0; i < length; i++) {
    const idx = bytes[i] % charset.length;
    tempPassword += charset[idx];
  }

  // Ensure password contains at least one digit and one letter when possible
  if (!includeSymbols && length >= 2) {
    const hasDigit = /[0-9]/.test(tempPassword);
    const hasLetter = /[A-Za-z]/.test(tempPassword);
    if (!hasDigit || !hasLetter) {
      // fallback: regenerate until both present (very unlikely; safe)
      return generateTempPassword(options);
    }
  }

  const hashedPassword = await bcrypt.hash(tempPassword, hashRounds);

  return { tempPassword, hashedPassword };
}

module.exports = { generateTempPassword };