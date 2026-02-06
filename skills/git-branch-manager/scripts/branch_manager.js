#!/usr/bin/env node

/**
 * Git 分支管理技能
 * 功能：从当前 feature/A 分支创建或更新对应的 feature/test/A 分支
 */

const { execSync } = require('child_process');
const fs = require('fs');

function runCommand(command, description) {
    console.log(`正在${description}...`);
    try {
        const result = execSync(command, { encoding: 'utf-8' });
        console.log(result);
        return result.trim();
    } catch (error) {
        console.error(`执行命令失败: ${command}`);
        console.error(error.message);
        throw error;
    }
}

function getCurrentBranch() {
    return runCommand('git rev-parse --abbrev-ref HEAD', '获取当前分支');
}

function branchExists(branchName) {
    try {
        execSync(`git show-ref --verify --quiet refs/heads/${branchName}`);
        return true;
    } catch (error) {
        return false;
    }
}

function main() {
    console.log('Git 分支管理技能启动...');

    try {
        const currentBranch = getCurrentBranch();
        console.log(`当前分支: ${currentBranch}`);

        // 检查是否为 feature/* 形式的分支
        if (!currentBranch.startsWith('feature/') || currentBranch.startsWith('feature/test/')) {
            console.error('当前不在 feature 分支上，或者已经是 feature/test 分支！');
            process.exit(1);
        }

        // 构建目标测试分支名称
        const featurePart = currentBranch.split('/').slice(1).join('/');
        const targetBranch = `feature/test/${featurePart}`;

        console.log(`目标分支: ${targetBranch}`);

        // 拉取最新的远程信息
        runCommand('git fetch origin', '拉取远程更新');

        // 检查目标分支是否存在
        if (branchExists(targetBranch)) {
            console.log(`分支 ${targetBranch} 已存在，将合并当前分支到目标分支`);

            // 切换到目标分支
            runCommand(`git checkout ${targetBranch}`, `切换到 ${targetBranch}`);

            // 拉取目标分支最新代码
            runCommand(`git pull origin ${targetBranch}`, `拉取 ${targetBranch} 分支最新代码`);

            // 合并当前分支到目标分支
            runCommand(`git merge ${currentBranch}`, `合并 ${currentBranch} 到 ${targetBranch}`);
        } else {
            console.log(`分支 ${targetBranch} 不存在，基于当前分支创建`);

            // 基于当前分支创建新的测试分支
            runCommand(`git checkout -b ${targetBranch}`, `基于 ${currentBranch} 创建新分支 ${targetBranch}`);
        }

        // 推送目标分支
        runCommand(`git push origin ${targetBranch}`, `推送 ${targetBranch} 分支`);

        // 检查是否安装了 GitHub CLI
        try {
            execSync('gh --version', { encoding: 'utf-8' });

            // 尝试创建 PR（如果不存在的话）
            console.log('检测到 GitHub CLI，正在检查 Pull Request...');
            try {
                // 获取远程PR列表，检查是否存在从目标分支到test分支的PR
                const prCheck = execSync(`gh pr list --head ${targetBranch} --json state --jq '.[0].state'`, { encoding: 'utf-8' });

                if (!prCheck || prCheck.trim() === "null") {
                    console.log(`正在创建 Pull Request...`);
                    runCommand(
                        `gh pr create --title "Merge ${targetBranch} to test" --body "Automated PR from ${currentBranch} via git branch manager skill\\n\\n- Source branch: ${currentBranch}\\n- Target branch: test" --base test --head ${targetBranch}`,
                        '创建 Pull Request'
                    );
                } else {
                    console.log(`Pull Request 已存在，无需重复创建`);
                }
            } catch (prError) {
                console.log(`PR操作失败，但分支已成功更新: ${prError.message}`);
            }
        } catch (error) {
            console.log(`\n分支操作完成！分支 ${targetBranch} 已推送至远程。`);
            console.log(`如需创建 Pull Request，请手动操作或安装 GitHub CLI。`);
        }

        // 切换回原分支
        runCommand(`git checkout ${currentBranch}`, `切换回 ${currentBranch}`);

        console.log('\n所有操作完成！分支已成功同步。');
    } catch (error) {
        console.error('\n操作过程中出现错误:', error.message);
        process.exit(1);
    }
}

main();