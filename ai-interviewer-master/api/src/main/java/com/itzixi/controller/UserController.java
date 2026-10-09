package com.itzixi.controller;

import com.itzixi.pojo.User;
import com.itzixi.service.UserService;
import com.itzixi.utils.IMoocJSONResult;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/user")
public class UserController {

    @Autowired
    private UserService userService;

    @PostMapping("/register")
    public IMoocJSONResult register(@RequestBody User user) {
        // 检查用户名是否已存在
        if (userService.findByUsername(user.getUsername()) != null) {
            return IMoocJSONResult.errorMsg("用户名已存在");
        }
        
        // 保存用户
        userService.save(user);
        return IMoocJSONResult.ok();
    }

    @PostMapping("/login")
    public IMoocJSONResult login(@RequestBody User user) {
        User existingUser = userService.findByUsername(user.getUsername());
        
        // 检查用户是否存在
        if (existingUser == null) {
            return IMoocJSONResult.errorMsg("用户不存在");
        }
        
        // 检查密码是否正确
        if (!existingUser.getPassword().equals(user.getPassword())) {
            return IMoocJSONResult.errorMsg("密码错误");
        }
        System.out.println("登录成功");
        // 返回用户信息（不包含密码）
        existingUser.setPassword(null);
        return IMoocJSONResult.ok(existingUser);
    }
    @PostMapping("/updatePassword")
    public IMoocJSONResult updatePassword(@RequestBody User user) {
        if (user.getId() == null) {
            return IMoocJSONResult.errorMsg("用户ID不能为空");
        }

        User existingUser = userService.findById(user.getId());

        // 检查用户是否存在
        if (existingUser == null) {
            return IMoocJSONResult.errorMsg("用户不存在");
        }

        // 检查原密码是否正确
        if (!existingUser.getPassword().equals(user.getOldPassword())) {
            return IMoocJSONResult.errorMsg("原密码错误");
        }

        // 检查新密码是否为空
        if (user.getPassword() == null || user.getPassword().trim().isEmpty()) {
            return IMoocJSONResult.errorMsg("新密码不能为空");
        }

        // 更新密码
        existingUser.setPassword(user.getPassword());
        try {
            userService.updatePassword(existingUser);
            return IMoocJSONResult.ok("密码修改成功");
        } catch (Exception e) {
            e.printStackTrace();
            return IMoocJSONResult.errorMsg("密码修改失败：" + e.getMessage());
        }
    }
}
