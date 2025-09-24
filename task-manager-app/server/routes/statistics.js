const express = require('express');
const Task = require('../models/Task');
const auth = require('../middleware/auth');

const router = express.Router();

// Get basic task statistics
router.get('/basic', auth, async (req, res) => {
  try {
    const userId = req.user._id;
    
    // Get all tasks for the user
    const tasks = await Task.find({ user: userId });
    
    const totalTasks = tasks.length;
    const completedTasks = tasks.filter(task => task.status === 'Completed').length;
    const pendingTasks = tasks.filter(task => task.status === 'Pending').length;
    const inProgressTasks = tasks.filter(task => task.status === 'In Progress').length;
    
    // Calculate overdue tasks (dueDate is in the past and status is not completed)
    const now = new Date();
    const overdueTasks = tasks.filter(task => 
      task.dueDate && 
      new Date(task.dueDate) < now && 
      task.status !== 'Completed'
    ).length;
    
    // Calculate completion rate
    const completionRate = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0;
    
    // Get tasks by priority
    const highPriorityTasks = tasks.filter(task => task.priority === 'High').length;
    const mediumPriorityTasks = tasks.filter(task => task.priority === 'Medium').length;
    const lowPriorityTasks = tasks.filter(task => task.priority === 'Low').length;
    
    res.json({
      totalTasks,
      completedTasks,
      pendingTasks,
      inProgressTasks,
      overdueTasks,
      completionRate,
      priority: {
        high: highPriorityTasks,
        medium: mediumPriorityTasks,
        low: lowPriorityTasks
      },
      status: {
        completed: completedTasks,
        pending: pendingTasks,
        inProgress: inProgressTasks
      }
    });
  } catch (error) {
    console.error('Error fetching basic statistics:', error);
    res.status(500).json({ message: 'Server error' });
  }
});

// Get productivity metrics (completion trends)
router.get('/productivity', auth, async (req, res) => {
  try {
    const userId = req.user._id;
    const { period = 'week' } = req.query;
    
    let startDate, endDate, groupBy;
    
    if (period === 'week') {
      startDate = new Date();
      startDate.setDate(startDate.getDate() - 7);
      endDate = new Date();
      groupBy = { $dateToString: { format: '%Y-%m-%d', date: '$createdAt' } };
    } else if (period === 'month') {
      startDate = new Date();
      startDate.setMonth(startDate.getMonth() - 1);
      endDate = new Date();
      groupBy = { $dateToString: { format: '%Y-%m-%d', date: '$createdAt' } };
    } else if (period === 'year') {
      startDate = new Date();
      startDate.setFullYear(startDate.getFullYear() - 1);
      endDate = new Date();
      groupBy = { $dateToString: { format: '%Y-%m', date: '$createdAt' } };
    } else {
      return res.status(400).json({ message: 'Invalid period. Use week, month, or year.' });
    }
    
    // Get tasks created in the period
    const createdTasks = await Task.aggregate([
      {
        $match: {
          user: userId,
          createdAt: { $gte: startDate, $lte: endDate }
        }
      },
      {
        $group: {
          _id: groupBy,
          created: { $sum: 1 }
        }
      },
      { $sort: { _id: 1 } }
    ]);
    
    // Get tasks completed in the period
    const completedTasks = await Task.aggregate([
      {
        $match: {
          user: userId,
          status: 'Completed',
          updatedAt: { $gte: startDate, $lte: endDate }
        }
      },
      {
        $group: {
          _id: groupBy,
          completed: { $sum: 1 }
        }
      },
      { $sort: { _id: 1 } }
    ]);
    
    // Merge the results
    const mergedData = {};
    
    createdTasks.forEach(item => {
      mergedData[item._id] = {
        date: item._id,
        created: item.created,
        completed: 0
      };
    });
    
    completedTasks.forEach(item => {
      if (mergedData[item._id]) {
        mergedData[item._id].completed = item.completed;
      } else {
        mergedData[item._id] = {
          date: item._id,
          created: 0,
          completed: item.completed
        };
      }
    });
    
    // Convert to array and sort
    const result = Object.values(mergedData).sort((a, b) => a.date.localeCompare(b.date));
    
    // Calculate productivity metrics
    const totalCreated = result.reduce((sum, item) => sum + item.created, 0);
    const totalCompleted = result.reduce((sum, item) => sum + item.completed, 0);
    const avgTasksPerDay = period === 'week' ? (totalCreated / 7).toFixed(1) : 
      period === 'month' ? (totalCreated / 30).toFixed(1) : 
        (totalCreated / 365).toFixed(1);
    
    res.json({
      period,
      data: result,
      metrics: {
        totalCreated,
        totalCompleted,
        avgTasksPerDay: parseFloat(avgTasksPerDay),
        completionRate: totalCreated > 0 ? Math.round((totalCompleted / totalCreated) * 100) : 0
      }
    });
  } catch (error) {
    console.error('Error fetching productivity metrics:', error);
    res.status(500).json({ message: 'Server error' });
  }
});

// Get recent activity (recently completed tasks)
router.get('/recent-activity', auth, async (req, res) => {
  try {
    const userId = req.user._id;
    const { limit = 10 } = req.query;
    
    const recentTasks = await Task.find({ 
      user: userId, 
      status: 'Completed' 
    })
      .sort({ updatedAt: -1 })
      .limit(parseInt(limit))
      .populate('category', 'name')
      .select('title description category priority updatedAt');
    
    res.json(recentTasks);
  } catch (error) {
    console.error('Error fetching recent activity:', error);
    res.status(500).json({ message: 'Server error' });
  }
});

// Get tasks due soon (next 7 days)
router.get('/due-soon', auth, async (req, res) => {
  try {
    const userId = req.user._id;
    const { days = 7 } = req.query;
    
    const now = new Date();
    const futureDate = new Date();
    futureDate.setDate(now.getDate() + parseInt(days));
    
    const dueSoonTasks = await Task.find({
      user: userId,
      status: { $ne: 'Completed' },
      dueDate: { $gte: now, $lte: futureDate }
    })
      .sort({ dueDate: 1 })
      .populate('category', 'name')
      .select('title description category priority dueDate status');
    
    res.json(dueSoonTasks);
  } catch (error) {
    console.error('Error fetching due soon tasks:', error);
    res.status(500).json({ message: 'Server error' });
  }
});

module.exports = router;
