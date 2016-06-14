function SDPT3solve(in_file)
%% in_file is a .mat file

[blk,At,C,b] = read_sedumi(in_file);
[obj,X,y,Z] = sqlp(blk,At,C,b);

%% Print out the objective in a way that will be easy to extract
disp('obj =');
disp(num2str(obj,12));
disp('>>');

%% Print out X in a way that will be easy to extract
for i=1:length(X)
    disp(['X{' num2str(i) '} =']);
    disp(num2str(X{i},12));
    disp('>>');
end

%% Not currently being used:
% disp('y=');
% disp(num2str(y,12));
% disp('Z=');
% for i=1:length(Z)
%     disp(num2str(Z{i},12));
% end

end
