import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  Home, 
  Video, 
  Layers, 
  Users, 
  Mic2, 
  Film, 
  Settings, 
  HelpCircle,
  Cpu
} from 'lucide-react';
import { RoutePath } from '../types';

const Sidebar: React.FC = () => {
  const navItems = [
    { icon: Home, label: '首页', path: RoutePath.HOME },
    { icon: Video, label: '单条制作', path: RoutePath.SINGLE_CREATE },
    { icon: Layers, label: '批量制作', path: RoutePath.BATCH_CREATE },
    { icon: Users, label: '数字人管理', path: RoutePath.AVATARS },
    { icon: Mic2, label: '音色管理', path: RoutePath.VOICES },
    { icon: Film, label: '作品库', path: RoutePath.WORKS },
    { icon: Settings, label: '设置', path: RoutePath.SETTINGS },
    { icon: HelpCircle, label: '帮助与反馈', path: RoutePath.HELP },
  ];

  return (
    <div className="w-64 h-screen bg-slate-900 text-white flex flex-col shadow-xl flex-shrink-0 z-20">
      <div className="p-6 border-b border-slate-800 flex items-center space-x-3">
        <div className="w-8 h-8 bg-indigo-500 rounded-lg flex items-center justify-center">
            <Cpu size={20} className="text-white" />
        </div>
        <div>
            <h1 className="text-lg font-bold leading-none">智影口播</h1>
            <span className="text-xs text-slate-400">AI Video Assistant</span>
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto py-4">
        <ul className="space-y-1 px-3">
          {navItems.map((item) => (
            <li key={item.path}>
              <NavLink
                to={item.path}
                className={({ isActive }) =>
                  `flex items-center px-4 py-3 rounded-lg transition-colors group ${
                    isActive
                      ? 'bg-indigo-600 text-white shadow-md'
                      : 'text-slate-400 hover:bg-slate-800 hover:text-white'
                  }`
                }
              >
                <item.icon size={20} className="mr-3" />
                <span className="font-medium text-sm">{item.label}</span>
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      <div className="p-4 border-t border-slate-800">
        <div className="bg-slate-800 rounded-lg p-3 text-xs text-slate-400">
          <div className="flex justify-between mb-1">
            <span>会员版</span>
            <span className="text-green-400">已激活</span>
          </div>
          <div className="w-full bg-slate-700 h-1.5 rounded-full mt-2">
            <div className="bg-indigo-500 h-1.5 rounded-full" style={{ width: '45%' }}></div>
          </div>
          <div className="mt-1 text-[10px] text-slate-500">模型存储: 45GB / 100GB</div>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;