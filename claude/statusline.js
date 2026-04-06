#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Read JSON from stdin
let input = '';
process.stdin.on('data', chunk => input += chunk);
process.stdin.on('end', () => {
  try {
    const data = JSON.parse(input);

    // ANSI color codes
    const colors = {
      reset: '\x1b[0m',
      cyan: '\x1b[36m',
      green: '\x1b[32m',
      yellow: '\x1b[33m',
      blue: '\x1b[34m',
      magenta: '\x1b[35m',
      gray: '\x1b[90m',
      red: '\x1b[31m',
      bold: '\x1b[1m',
    };

    const ccSegments = []; // Claude Code line
    const allGhLines = []; // Array of GH lines (one per repo)

    // Helper function to find all repos touched in this session
    function findTouchedRepos() {
      const repos = new Set();
      const transcriptPath = data.transcript_path;

      // Always include current directory if it's a git repo
      const currentDir = data.workspace?.current_dir || data.cwd;
      if (currentDir && fs.existsSync(currentDir)) {
        try {
          execSync('git rev-parse --git-dir', { cwd: currentDir, stdio: 'ignore' });
          repos.add(currentDir);
        } catch (e) {
          // Not a git repo
        }
      }

      // Parse transcript for git commands in other repos
      if (transcriptPath && fs.existsSync(transcriptPath)) {
        try {
          const transcript = fs.readFileSync(transcriptPath, 'utf8');

          // Transcript is JSONL format (one JSON per line)
          const lines = transcript.split('\n');

          for (const line of lines) {
            if (!line.trim()) continue;

            try {
              const entry = JSON.parse(line);

              // Look for Bash tool uses in assistant messages
              if (entry.type === 'assistant' && entry.message && entry.message.content) {
                for (const content of entry.message.content) {
                  if (content.type === 'tool_use' && content.name === 'Bash' && content.input) {
                    const command = content.input.command;

                    if (command && command.includes('git ')) {
                      // Extract working directory from command
                      const cdMatch = command.match(/cd\s+"([^"]+)"/);
                      if (cdMatch) {
                        const repoPath = cdMatch[1];
                        if (fs.existsSync(repoPath)) {
                          try {
                            execSync('git rev-parse --git-dir', { cwd: repoPath, stdio: 'ignore' });
                            repos.add(repoPath);
                          } catch (e) {
                            // Not a git repo
                          }
                        }
                      }
                    }
                  }
                }
              }
            } catch (e) {
              // Skip invalid JSON lines
            }
          }
        } catch (e) {
          // Transcript parsing failed
        }
      }

      return Array.from(repos);
    }

    // Line 1: Claude Code info
    ccSegments.push(`${colors.yellow}${colors.bold}CC:${colors.reset}`);

    // Helper function to generate GH line for a repo
    function generateGhLine(repoPath) {
      const ghSegments = [];
      ghSegments.push(`${colors.blue}${colors.bold}GH:${colors.reset}`);

      try {
        const repoName = path.basename(repoPath);

        const branch = execSync('git rev-parse --abbrev-ref HEAD', {
          cwd: repoPath,
          encoding: 'utf8',
          stdio: ['pipe', 'pipe', 'ignore']
        }).trim();

        let branchInfo = `${repoName} (⎇ ${branch}`;

        // Check sync status (ahead/behind remote)
        try {
          const status = execSync('git status -sb --porcelain', {
            cwd: repoPath,
            encoding: 'utf8',
            stdio: ['pipe', 'pipe', 'ignore']
          }).trim();

          const firstLine = status.split('\n')[0];
          const aheadMatch = firstLine.match(/ahead (\d+)/);
          const behindMatch = firstLine.match(/behind (\d+)/);

          if (aheadMatch) {
            branchInfo += ` ${colors.green}↑${aheadMatch[1]}${colors.reset}`;
          }
          if (behindMatch) {
            branchInfo += ` ${colors.yellow}↓${behindMatch[1]}${colors.reset}`;
          }
        } catch (e) {
          // No remote
        }

        // Check for dirty workspace
        try {
          const statusShort = execSync('git status --porcelain', {
            cwd: repoPath,
            encoding: 'utf8',
            stdio: ['pipe', 'pipe', 'ignore']
          }).trim();

          if (statusShort.length > 0) {
            branchInfo += ` ${colors.red}⚡${colors.reset}`;
          }
        } catch (e) {
          // Error checking status
        }

        // Get last commit time
        try {
          const commitTime = execSync('git log -1 --format=%ar', {
            cwd: repoPath,
            encoding: 'utf8',
            stdio: ['pipe', 'pipe', 'ignore']
          }).trim();

          const shortTime = commitTime
            .replace(' seconds', 's')
            .replace(' second', 's')
            .replace(' minutes', 'm')
            .replace(' minute', 'm')
            .replace(' hours', 'h')
            .replace(' hour', 'h')
            .replace(' days', 'd')
            .replace(' day', 'd')
            .replace(' weeks', 'w')
            .replace(' week', 'w')
            .replace(' months', 'mo')
            .replace(' month', 'mo');

          branchInfo += ` ${colors.gray}${shortTime})${colors.reset}`;
        } catch (e) {
          branchInfo += ')';
        }

        ghSegments.push(`${colors.magenta}${branchInfo}${colors.reset}`);

        // Check CI/CD status
        try {
          execSync('gh --version', { stdio: 'ignore' });

          const workflowStatus = execSync('gh run list --limit 1 --json status,conclusion', {
            cwd: repoPath,
            encoding: 'utf8',
            stdio: ['pipe', 'pipe', 'ignore']
          });

          const runs = JSON.parse(workflowStatus);
          if (runs && runs.length > 0) {
            const run = runs[0];
            let statusIcon = '';
            let statusColor = colors.gray;

            if (run.status === 'completed') {
              if (run.conclusion === 'success') {
                statusIcon = '✅';
                statusColor = colors.green;
              } else if (run.conclusion === 'failure') {
                statusIcon = '❌';
                statusColor = colors.red;
              } else if (run.conclusion === 'cancelled') {
                statusIcon = '⚠️';
                statusColor = colors.yellow;
              }
            } else if (run.status === 'in_progress') {
              statusIcon = '⏳';
              statusColor = colors.yellow;
            }

            if (statusIcon) {
              ghSegments.push(`CI ${statusColor}${statusIcon}${colors.reset}`);
            }
          }
        } catch (ghError) {
          // gh not available or no workflows
        }

        return ghSegments.join(` ${colors.gray}│${colors.reset} `);
      } catch (e) {
        return null;
      }
    }

    // 1. Model info
    const modelName = data.model?.display_name || data.model?.id || 'Claude';
    ccSegments.push(`${colors.cyan}${colors.bold}${modelName}${colors.reset}`);

    // 3. Current directory
    const currentDir = data.workspace?.current_dir || data.cwd || '';
    if (currentDir) {
      const currentDirName = path.basename(currentDir) || currentDir;
      ccSegments.push(`${colors.blue}${currentDirName}${colors.reset}`);
    }

    // 4. Python virtual environment
    if (process.env.VIRTUAL_ENV) {
      const venvName = path.basename(process.env.VIRTUAL_ENV);
      ccSegments.push(`${colors.green}🐍 ${venvName}${colors.reset}`);
    }

    // 5. Current context window usage (not cumulative)
    // Opus 4.6 and Sonnet 4.6 have 1M context; all others 200K
    const modelId = data.model?.id || '';
    const modelDisplay = data.model?.display_name || '';
    const is1M = modelId.includes('opus-4-6') || modelId.includes('sonnet-4-6')
              || modelDisplay.includes('1M context');
    const TOKEN_LIMIT = is1M ? 1000000 : 200000;
        // Small baseline overhead for uncached portions of system prompt
    // Most system/tool tokens are captured in cache_read_input_tokens
    // This accounts for the small gap between transcript and /context
    const BASELINE_OVERHEAD = 6000;
    const LAG_BUFFER_PERCENT = 0.05; // 5% buffer for lag
    let contextTokens = 0;

    // Get token usage from last assistant message in transcript
    // Total context = input_tokens + cache_creation_input_tokens + cache_read_input_tokens
    const transcriptPath = data.transcript_path;
    if (transcriptPath && fs.existsSync(transcriptPath)) {
      try {
        const transcript = fs.readFileSync(transcriptPath, 'utf8');
        const tlines = transcript.trim().split('\n');

        // Find last assistant message with usage data
        for (let i = tlines.length - 1; i >= 0; i--) {
          try {
            const entry = JSON.parse(tlines[i]);
            if (entry.type === 'assistant' && entry.message && entry.message.usage) {
              const usage = entry.message.usage;
              // Add baseline overhead to match /context display
              contextTokens = BASELINE_OVERHEAD +
                             (usage.input_tokens || 0) +
                             (usage.cache_creation_input_tokens || 0) +
                             (usage.cache_read_input_tokens || 0);
              break;
            }
          } catch (e) {
            // Skip invalid JSON lines
          }
        }
      } catch (e) {
        // Token parsing failed, skip
      }
    }

    if (contextTokens > 0) {
      const bufferedTokens = Math.round(contextTokens * (1 + LAG_BUFFER_PERCENT));
      const percentUsed = Math.round((bufferedTokens / TOKEN_LIMIT) * 100);
      const percentRemaining = 100 - percentUsed;

      // Color code based on usage
      let tokenColor = colors.green;
      if (percentUsed >= 80) {
        tokenColor = colors.red;
      } else if (percentUsed >= 50) {
        tokenColor = colors.yellow;
      }

      const tokenInfo = `${(bufferedTokens / 1000).toFixed(1)}k (${percentRemaining}% left)`;
      ccSegments.push(`${tokenColor}📊 ${tokenInfo}${colors.reset}`);
    }

    // 6. Code changes
    if (data.cost?.total_lines_added || data.cost?.total_lines_removed) {
      const added = data.cost.total_lines_added || 0;
      const removed = data.cost.total_lines_removed || 0;
      if (added > 0 || removed > 0) {
        ccSegments.push(`📝 ${colors.green}+${added}${colors.reset}/${colors.red}-${removed}${colors.reset}`);
      }
    }

    // 7. Generate GH lines for all touched repos
    const touchedRepos = findTouchedRepos();
    for (const repoPath of touchedRepos) {
      const ghLine = generateGhLine(repoPath);
      if (ghLine) {
        allGhLines.push(ghLine);
      }
    }

    // Output multi-line statusline
    const ccLine = ccSegments.join(` ${colors.gray}│${colors.reset} `);
    console.log(ccLine);

    // Output all GH lines
    for (const ghLine of allGhLines) {
      console.log(ghLine);
    }

  } catch (error) {
    // Fallback to just showing model name
    try {
      const data = JSON.parse(input);
      const modelName = data.model?.display_name || 'Claude';
      console.log(modelName);
    } catch (e) {
      console.log('Claude');
    }
  }
});
