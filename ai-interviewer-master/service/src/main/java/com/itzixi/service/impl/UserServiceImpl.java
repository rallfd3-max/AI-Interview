package com.itzixi.service.impl;

import com.itzixi.mapper.UserMapper;
import com.itzixi.pojo.User;
import com.itzixi.service.UserService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

@Service
public class UserServiceImpl implements UserService {

    @Autowired
    private UserMapper userMapper;

    @Override
    public User findByUsername(String username) {
        return userMapper.findByUsername(username);
    }

    @Override
    public User findById(Integer id) {
        return userMapper.findById(id);
    }
    @Override
    public int save(User user) {
        return userMapper.save(user);
    }
    @Override
    public int updatePassword(User user) {
        return userMapper.updatePassword(user);
    }
}
